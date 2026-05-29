const steps = Array.from(document.querySelectorAll(".step"));

const btnProximo = document.getElementById("btnProximo");
const btnVoltar = document.getElementById("btnVoltar");
const btnIniciar = document.getElementById("btnIniciar");
const btnPausar = document.getElementById("btnPausar");
const btnScanner = document.getElementById("btnScanner");
const btnSemCodigo = document.getElementById("btnSemCodigo");
const btnPararScanner = document.getElementById("btnPararScanner");

const formEstoque = document.getElementById("formEstoque");
const perguntaAtual = document.getElementById("perguntaAtual");
const progressBar = document.getElementById("progressBar");

let currentStep = 0;
let conversaAtiva = false;
let recognition = null;
let html5QrCode = null;
let scannerAtivo = false;
let aguardandoConfirmacao = false;

const fields = [
  {
    id: "codigo_barras",
    pergunta: "O material possui código de barras? Responda sim ou não.",
    limpar: (v) => v.replace(/\D/g, ""),
    optional: true
  },
  {
    id: "produto",
    pergunta: "Qual o produto?",
    limpar: (v) => v.toUpperCase().trim()
  },
  {
    id: "quantidade",
    pergunta: "Qual a quantidade em estoque?",
    limpar: (v) => {
      const num = v.match(/\d+/);
      return num ? num[0] : "";
    }
  },
  {
    id: "lote",
    pergunta: "Qual o lote?",
    limpar: (v) => v.toUpperCase().replace(/\s+/g, "").trim()
  },
  {
    id: "validade",
    pergunta: "Qual o vencimento? Fale dia, mês e ano.",
    limpar: normalizarData
  }
];

function showStep(index, falar = true) {
  steps.forEach((step, i) => step.classList.toggle("active", i === index));
  currentStep = index;

  const percent = ((index + 1) / steps.length) * 100;
  progressBar.style.width = `${percent}%`;

  btnVoltar.style.display = index === 0 ? "none" : "block";
  btnProximo.style.display = index === steps.length - 1 ? "none" : "block";

  if (index < fields.length) {
    aguardandoConfirmacao = false;
    perguntaAtual.textContent = fields[index].pergunta;
    const input = document.getElementById(fields[index].id);
    if (input) input.focus();

    if (conversaAtiva && falar) perguntarEEscutar(fields[index].pergunta);
  } else {
    atualizarRevisao();
    aguardandoConfirmacao = true;
    const resumo = montarResumoFalado();
    perguntaAtual.textContent = "Confira os dados. Responda sim para salvar ou não para corrigir.";
    if (conversaAtiva && falar) perguntarEEscutar(`${resumo}. Está correto? Responda sim para salvar ou não para corrigir.`);
  }
}

function validarEtapa() {
  if (currentStep >= fields.length) return true;

  const field = fields[currentStep];
  const input = document.getElementById(field.id);
  input.value = field.limpar(input.value);

  if (!field.optional && !input.value.trim()) {
    perguntaAtual.textContent = "Campo vazio. Vou perguntar novamente.";
    if (conversaAtiva) perguntarEEscutar("Não entendi. " + field.pergunta);
    return false;
  }

  if (field.id === "validade" && !/^\d{2}\/\d{2}\/\d{4}$/.test(input.value)) {
    perguntaAtual.textContent = "Vencimento inválido. Use dia, mês e ano.";
    if (conversaAtiva) perguntarEEscutar("O vencimento precisa ter dia, mês e ano. " + field.pergunta);
    return false;
  }

  return true;
}

async function proximo() {
  if (!validarEtapa()) return;

  if (currentStep === 0) {
    const codigo = document.getElementById("codigo_barras").value.trim();
    if (codigo) await buscarCodigo();
    else showStep(1);
    return;
  }

  showStep(currentStep + 1);
}

function voltar() {
  showStep(Math.max(0, currentStep - 1));
}

function atualizarRevisao() {
  const codigo = document.getElementById("codigo_barras").value || "Sem código";
  document.getElementById("r_codigo").textContent = codigo;
  document.getElementById("r_produto").textContent = document.getElementById("produto").value;
  document.getElementById("r_quantidade").textContent = document.getElementById("quantidade").value;
  document.getElementById("r_lote").textContent = document.getElementById("lote").value;
  document.getElementById("r_validade").textContent = document.getElementById("validade").value;
}

function montarResumoFalado() {
  const codigo = document.getElementById("codigo_barras").value || "sem código";
  const produto = document.getElementById("produto").value;
  const quantidade = document.getElementById("quantidade").value;
  const lote = document.getElementById("lote").value;
  const validade = document.getElementById("validade").value;

  return `Produto ${produto}. Quantidade ${quantidade}. Lote ${lote}. Vencimento ${validade}`;
}

function normalizarData(valor) {
  valor = valor.trim().replaceAll("-", "/").replaceAll(".", "/");

  const dataComBarras = valor.match(/(\d{2})\/(\d{2})\/(\d{4})/);
  if (dataComBarras) return `${dataComBarras[1]}/${dataComBarras[2]}/${dataComBarras[3]}`;

  const numeros = valor.match(/\d+/g);
  if (numeros && numeros.length >= 3) {
    const dia = numeros[0].padStart(2, "0");
    const mes = numeros[1].padStart(2, "0");
    let ano = numeros[2];
    if (ano.length === 2) ano = "20" + ano;
    return `${dia}/${mes}/${ano}`;
  }

  return valor;
}

function falarTexto(texto) {
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) return resolve();

    window.speechSynthesis.cancel();

    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = "pt-BR";
    fala.rate = 1;
    fala.pitch = 1;
    fala.onend = () => resolve();
    fala.onerror = () => resolve();

    window.speechSynthesis.speak(fala);
  });
}

async function perguntarEEscutar(texto) {
  if (!conversaAtiva) return;

  await falarTexto(texto);

  if (!conversaAtiva) return;

  setTimeout(() => {
    iniciarEscuta();
  }, 250);
}

function iniciarEscuta() {
  if (!conversaAtiva || !recognition) return;

  try {
    perguntaAtual.textContent = "Ouvindo...";
    recognition.start();
  } catch (e) {
    perguntaAtual.textContent = "Não consegui iniciar o microfone. Clique em iniciar novamente.";
  }
}

async function buscarCodigo() {
  const codigoInput = document.getElementById("codigo_barras");
  codigoInput.value = codigoInput.value.replace(/\D/g, "");

  if (!codigoInput.value) {
    showStep(1);
    return;
  }

  perguntaAtual.textContent = "Buscando código no Excel...";

  try {
    const resp = await fetch("/buscar_codigo", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({codigo: codigoInput.value})
    });

    const data = await resp.json();

    if (data.found) {
      document.getElementById("produto").value = data.produto || "";
      document.getElementById("validade").value = data.validade || "";
      if (conversaAtiva) await falarTexto(`Produto encontrado: ${data.produto}.`);
      showStep(2, true);
    } else {
      if (conversaAtiva) await falarTexto("Produto não encontrado. Vamos cadastrar completo.");
      showStep(1, true);
    }

  } catch (e) {
    perguntaAtual.textContent = "Erro ao buscar código. Vou seguir manualmente.";
    if (conversaAtiva) await falarTexto("Erro ao buscar código. Vamos seguir manualmente.");
    showStep(1, true);
  }
}

async function iniciarScanner() {
  if (!window.Html5Qrcode) {
    alert("Biblioteca de leitura não carregou. Digite o código ou continue sem código.");
    return;
  }

  if (scannerAtivo) return;
  html5QrCode = new Html5Qrcode("reader");

  try {
    scannerAtivo = true;
    btnScanner.classList.add("hidden");
    btnPararScanner.classList.remove("hidden");
    document.getElementById("reader").classList.remove("hidden");

    await html5QrCode.start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: { width: 260, height: 140 },
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E
        ]
      },
      async (decodedText) => {
        document.getElementById("codigo_barras").value = decodedText.replace(/\D/g, "");
        await pararScanner();
        if (conversaAtiva) await falarTexto("Código lido.");
        await buscarCodigo();
      },
      () => {}
    );
  } catch (err) {
    scannerAtivo = false;
    btnScanner.classList.remove("hidden");
    btnPararScanner.classList.add("hidden");
    perguntaAtual.textContent = "Não consegui abrir a câmera. Digite o código ou continue sem código.";
    alert("Não consegui abrir a câmera. Talvez precise de HTTPS ou permissão da câmera.");
  }
}

async function pararScanner() {
  if (html5QrCode && scannerAtivo) {
    try {
      await html5QrCode.stop();
      await html5QrCode.clear();
    } catch (e) {}
  }

  scannerAtivo = false;
  btnScanner.classList.remove("hidden");
  btnPararScanner.classList.add("hidden");
  document.getElementById("reader").classList.add("hidden");
}

btnScanner.addEventListener("click", iniciarScanner);
btnPararScanner.addEventListener("click", pararScanner);

btnSemCodigo.addEventListener("click", async () => {
  document.getElementById("codigo_barras").value = "";
  await pararScanner();
  if (conversaAtiva) await falarTexto("Tudo bem. Vamos continuar sem código de barras.");
  showStep(1, true);
});

btnProximo.addEventListener("click", proximo);
btnVoltar.addEventListener("click", voltar);

btnIniciar.addEventListener("click", async () => {
  conversaAtiva = true;
  btnIniciar.classList.add("hidden");
  btnPausar.classList.remove("hidden");
  await perguntarEEscutar("Conversa iniciada. O material possui código de barras? Responda sim ou não.");
});

btnPausar.addEventListener("click", () => {
  conversaAtiva = false;
  btnPausar.classList.add("hidden");
  btnIniciar.classList.remove("hidden");
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  try { recognition && recognition.stop(); } catch(e) {}
  perguntaAtual.textContent = "Conversa pausada.";
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  perguntaAtual.textContent = "Este navegador pode não aceitar conversa por voz. Use os botões e campos manuais.";
} else {
  recognition = new SpeechRecognition();
  recognition.lang = "pt-BR";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = async (event) => {
    const respostaOriginal = event.results[0][0].transcript;
    const resposta = respostaOriginal.toLowerCase().trim();

    perguntaAtual.textContent = `Entendi: ${respostaOriginal}`;

    if (resposta.includes("pausar")) {
      conversaAtiva = false;
      btnPausar.classList.add("hidden");
      btnIniciar.classList.remove("hidden");
      await falarTexto("Conversa pausada.");
      return;
    }

    if (resposta.includes("repetir")) {
      if (currentStep < fields.length) await perguntarEEscutar(fields[currentStep].pergunta);
      else await perguntarEEscutar("Está correto? Responda sim para salvar ou não para corrigir.");
      return;
    }

    if (resposta.includes("voltar")) {
      voltar();
      return;
    }

    if (aguardandoConfirmacao) {
      if (resposta.includes("sim") || resposta.includes("correto") || resposta.includes("salvar")) {
        formEstoque.submit();
        return;
      }

      if (resposta.includes("não") || resposta.includes("nao") || resposta.includes("corrigir")) {
        await falarTexto("Tudo bem. Voltando para o produto.");
        showStep(1, true);
        return;
      }

      await perguntarEEscutar("Não entendi. Está correto? Responda sim ou não.");
      return;
    }

    if (currentStep === 0) {
      if (resposta.includes("sim") || resposta.includes("tem") || resposta.includes("possui")) {
        await falarTexto("Abra a câmera ou digite o código.");
        return;
      }

      if (resposta.includes("não") || resposta.includes("nao") || resposta.includes("sem código") || resposta.includes("sem codigo")) {
        document.getElementById("codigo_barras").value = "";
        await falarTexto("Tudo bem. Vamos continuar sem código de barras.");
        showStep(1, true);
        return;
      }
    }

    if (currentStep < fields.length) {
      const field = fields[currentStep];
      const input = document.getElementById(field.id);

      input.value = field.limpar(respostaOriginal);

      if (!input.value && !field.optional) {
        await perguntarEEscutar("Não entendi. " + field.pergunta);
        return;
      }

      await falarTexto(`Entendi: ${input.value || "sem código"}`);
      await proximo();
    }
  };

  recognition.onerror = async () => {
    perguntaAtual.textContent = "Não consegui ouvir. Vou perguntar novamente.";
    if (conversaAtiva) {
      if (currentStep < fields.length) await perguntarEEscutar(fields[currentStep].pergunta);
      else await perguntarEEscutar("Está correto? Responda sim para salvar ou não para corrigir.");
    }
  };

  recognition.onend = () => {
    // Não reinicia aqui para evitar loop quando o navegador encerra sozinho.
  };
}

showStep(0, false);
