# Samsung Tizen TV — Jellyfin por sideload, sem anúncios e com tema minimalista

> **EN:** Field-tested guide to put **Jellyfin** on a Samsung Tizen TV (2017+ / Tizen 3.0+) without Tizen Studio,
> drive the TV over its network remote API (including typing text), block Samsung ads/ACR telemetry via DNS and
> apply a minimal, faster Jellyfin theme. Docs in Brazilian Portuguese; agent instructions in English in [`AGENTS.md`](AGENTS.md).

Guia completo, testado numa **Samsung UE58RU7100KXXU (58", 2019, Tizen 5.0)**, para auditar a TV pela rede,
ativar o modo desenvolvedor, instalar o **Jellyfin** por sideload, bloquear anúncios/telemetria com DNS e deixar
a navegação mais limpa e rápida. Tudo pela rede, a partir de um computador, usando a API de controle remoto
da própria TV — inclusive para digitar o DNS e o endereço do servidor quando o controle não tem teclado numérico.

## Compatibilidade

| Linha Samsung | Ano | Tizen | Funciona? |
|---|---|---|---|
| M / MU / Q7–Q9 | 2017 | 3.0 | sim |
| N / NU / Q6–Q9 | 2018 | 4.0 | sim |
| **R / RU / Q6–Q9** | **2019** | **5.0** | **sim — este guia** |
| T / TU / Q6–Q9 | 2020 | 5.5 | sim |
| AU / QN | 2021 | 6.0 | sim |
| BU / QN / S9 | 2022–2024 | 6.5–8.0 | sim; alguns modelos desligam o modo dev sozinhos ao reiniciar |
| Séries H / J (Orsay) | ≤ 2016 | — | não (sistema Orsay, outro instalador) |

Placeholders usados: `TV_IP` (IP da TV), `PC_IP` (IP do computador), `JELLYFIN_HOST:8096` (seu servidor).
Substitua pelos seus. Firmware citado (`T-MSLDEUC`) é **só** da linha RU7100 região EU — procure o da sua TV
no Download Center da Samsung pelo código completo do modelo.

> Instruções para agentes de IA (em inglês): [`AGENTS.md`](AGENTS.md). Anotações brutas de campo: [`docs/NOTAS.md`](docs/NOTAS.md).

## Resumo do que foi feito

| Etapa | Resultado |
|---|---|
| Descoberta na rede | TV responde em `http://TV_IP:8001/api/v2/`; mDNS `TIZEN.local` / `_airplay._tcp` |
| Auditoria de software | Tizen 5.0, portas 8001/8002/8080/7678/9197/15500/26101/49072; modo dev estava **off**; firmware não exposto pela API |
| Firmware oficial atual | **T-MSLDEUC 1500.9** (05/02/2025, 1,33 GB) — só para região EU/IE |
| Modo desenvolvedor | Ativado com `12345` enviado pela API (controle slim não tem números) |
| Jellyfin | Sideload em 16 s via Docker (`georift/install-jellyfin-tizen`), app id `AprZAARz4r.Jellyfin` |
| Servidor | `http://JELLYFIN_HOST:8096` (Jellyfin 12.2.0, Quick Connect ligado) digitado pela API |
| DNS | AdGuard `94.140.14.14` — bloqueia `samsungads.com` e `samsungacr.com` (ACR), mantém atualizações |
| Android TV? | **Não é possível** nesse hardware (bootloader travado). Alternativa: box por HDMI |

## 1. Encontrar a TV

```bash
scripts/find-tv.sh            # varre a /24 e mostra quem responde em :8001
scripts/tvinfo.sh TV_IP
```

A TV expõe em `http://IP:8001/api/v2/` modelo, serial, estado de energia, `developerMode` e `developerIP`.
O campo `firmwareVersion` vem sempre `"Unknown"` nesse modelo — a versão só aparece em
*Configurações → Suporte → Sobre esta TV*.

## 2. Controle remoto pela rede

`scripts/tvkeys.py` fala com `wss://IP:8002/api/v2/channels/samsung.remote.control`. Na primeira vez a TV
pergunta **"Permitir TizenCtl?"** — aceite; o token fica em `scripts/.tv.token` e não pergunta mais.

```bash
scripts/tvkeys.py KEY_HOME                               # tecla
scripts/tvkeys.py KEY_RETURN SLEEP1 KEY_MENU             # sequência com pausa
scripts/tvkeys.py "TEXT:JELLYFIN_HOST:8096"              # digita texto num campo com teclado aberto
scripts/tvkeys.py --launch AprZAARz4r.Jellyfin           # abre um app
KEYDELAY=0.3 scripts/tvkeys.py KEY_1 KEY_2 KEY_3 KEY_4 KEY_5
```

Códigos úteis: `KEY_HOME KEY_MENU KEY_RETURN KEY_ENTER KEY_UP/DOWN/LEFT/RIGHT KEY_0..KEY_9 KEY_SOURCE KEY_POWER`.

## 3. Modo desenvolvedor (Tizen 5.0)

1. **Home → Apps** — a tela da loja precisa **carregar com internet**. Se aparecer erro do TV Plus
   ("check your network settings"), o atalho é ignorado; resolva a rede antes.
2. Digite **1 2 3 4 5** (ou `scripts/tvkeys.py KEY_1 KEY_2 KEY_3 KEY_4 KEY_5`).
3. Janela *Developer mode* → **On** → *Host PC IP* = IP do computador → **OK** → desligar e ligar a TV.
4. Conferir: `scripts/tvinfo.sh` deve mostrar `developerMode 1`.

Se o foco estiver em "Entrar", os dígitos abrem o login da conta Samsung: feche com *Return* e **não digite nada**.

## 4. Instalar o Jellyfin

```bash
brew install colima && colima start --cpu 2 --memory 2   # macOS sem Docker Desktop
scripts/install-jellyfin.sh TV_IP
```

Saída esperada: `Installed the package: Id(AprZAARz4r.Jellyfin)`. Depois:
`scripts/tvkeys.py --launch AprZAARz4r.Jellyfin` → *Add Server* → `JELLYFIN_HOST:8096` → login
(ou **Quick Connect**, aprovando o código em `http://JELLYFIN_HOST:8096/web/`).

## 5. Home mais limpa e rápida

O modo desenvolvedor **não dá root** (`sdbd_rootperm disabled`) e **recusa remover apps da Samsung**
(testado). O que funciona de verdade:

**a) DNS com bloqueio (maior impacto).** *Configurações → Geral → Rede → Status da rede →
Configurações de IP → Config. DNS → Inserir manualmente* → `94.140.14.14`.
Verificado com `dig`: bloqueia `samsungads.com`, `config.samsungads.com`, `samsungacr.com`,
`log-config.samsungacr.com`; libera `www.samsungotn.net` (firmware) e `api.samsungosp.com` (conta).

> O campo de IP **avança sozinho ao completar 3 dígitos**. Pela API: `KEY_9 KEY_4 KEY_RIGHT KEY_1 KEY_4 KEY_0 KEY_1 KEY_4 KEY_RIGHT KEY_1 KEY_4`, depois `KEY_ENTER`, `KEY_DOWN KEY_DOWN KEY_ENTER` no botão OK.

**b) Smart Hub.** *Geral → Smart Hub → Termos e políticas*: desmarcar anúncios baseados em interesse e
serviço de informações de visualização. *Geral → Recursos inteligentes*: *Executar Smart Hub
automaticamente* e *Executar último app* em **Off**.

**c) Barra da Home.** Segurar OK em um ícone → *Remover* (TV Plus, Rakuten, DAZN, Channel 4, RTE,
Internet, Gallery). *Mover* o Jellyfin para a primeira posição.

**d) Fluidez.** Atualizar para o firmware 1500.9 e depois *Suporte → Autodiagnóstico → Redefinir Smart Hub*
(reinstalar o Jellyfin se sumir — 16 s).

## 6. Tema minimalista do Jellyfin

Automático (CSS + preferências de exibição de todos os usuários):

```bash
JF_URL=http://JELLYFIN_HOST:8096 JF_KEY=<api key> scripts/jellyfin-apply.sh
```

Manual: `theme/jellyfin-minimal.css` → colar em **Dashboard → General → Custom CSS**. Fundo sólido sem blur
(mais leve no Tizen), sem abas no topo, cards sem sombra, foco em destaque, fontes maiores.
Seções da Home se ajustam por usuário em *Perfil → Tela inicial*.

## 7. Fechar

Ao terminar, **desligue o modo desenvolvedor** (Apps → `12345` → Off → reiniciar). O Jellyfin continua
instalado; a porta 26101 (sdb) fecha.

## 8. Jellyfin mais rápido no Tizen (direcionais travando)

O app Tizen do Jellyfin é a interface web rodando no Chromium embarcado de uma TV de 2019 — tudo que reduz
pintura de tela ajuda **muito**:

**No servidor (admin → Dashboard):**
- *General → Custom CSS*: `theme/jellyfin-minimal.css` (fundo sólido, sem blur/backdrop, animações ~0).
- *Playback → Transcoding*: garanta aceleração de hardware ligada no servidor; a TV RU7100 reproduz
  H.264/HEVC direto — evite transcodificar.

**Por usuário (Perfil → Exibição / Tela inicial), na própria TV ou pela web:**
- *Exibição*: **desligar** "Backdrops", "Músicas-tema", "Vídeos-tema", "Mostrar faixa de progresso nos cards";
  *Densidade de detalhes* baixa; *Protetor de tela* = nenhum.
- *Tela inicial*: deixar só **Continuar assistindo**, **Próximo episódio** e **Minha mídia**; as seções
  "Adicionados recentemente" de cada biblioteca carregam dezenas de capas a cada foco.
- *Bibliotecas*: ordenar por nome, visualização *Pôster* (não *Banner/Lista com arte*).

**Na TV:**
- Modo desenvolvedor **Off** depois de instalar (o `sdbd` e o logger de debug consomem CPU).
- *Configurações → Geral → Recursos inteligentes*: autorun do Smart Hub Off.
- *Configurações → Geral → Gerenciador do sistema → Hora → Modo de suspensão*: desligado.
- Reiniciar de verdade de tempos em tempos (segurar Power até reiniciar) — a TV só "dorme" por padrão e
  a memória do Chromium não é liberada.

## Licença

MIT.
