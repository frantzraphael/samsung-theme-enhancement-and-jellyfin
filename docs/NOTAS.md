# Notas de campo — exemplo: Samsung UE58RU7100KXXU — 2026-10-31

## Descoberta
- Varredura: ping sweep sua rede /24 + arp -an + dns-sd -B (_airplay._tcp achou "Samsung 7 Series (58)").
- TV: TV_IP, MAC aa:bb:cc:dd:ee:ff, host TIZEN.local, cabeada, Tizen 5.0, modelo UE58RU7100KXXU (2019, RU7100, regiao EU/IE).
- API: http://IP:8001/api/v2/ (firmwareVersion "Unknown" - nao exposto). UPnP :9197/dmr e :7678/nservice. AirPlay :49072.
- Portas: 8001 8002 8080 7678 9197 15500 26101(sdb) 49072.
- Firmware oficial atual: T-MSLDEUC 1500.9 (05/02/2025, 1.33 GB). NAO usar T-MSLAKUC (Americas).
- Jellyfin server: http://JELLYFIN_HOST:8096 (v12.2.0).

## Controle remoto por rede (funcionou)
- wss://IP:8002/api/v2/channels/samsung.remote.control?name=<base64>&token=<tok>
- 1a conexao: TV mostra "Permitir <nome>?" -> aceitar; resposta ms.channel.connect traz data.token (salvar, reutilizar).
- Mensagem: {"method":"ms.remote.control","params":{"Cmd":"Click","DataOfCmd":"KEY_1","Option":"false","TypeOfRemote":"SendRemoteKey"}}
- Lancar app: {"method":"ms.channel.emit","params":{"event":"ed.apps.launch","to":"host","data":{"appId":"AprZAARz4r.Jellyfin","action_type":"NATIVE_LAUNCH"}}}
- Scripts: tvkeys.py (stdlib puro, sem websocket-client), tvlaunch.py.

## Modo desenvolvedor (Tizen 5.0)
- Home -> Apps (tela da loja CARREGADA com internet) -> digitar 12345 -> janela Developer mode -> On -> Host PC IP = IP do Mac -> reiniciar TV.
- Armadilhas: (1) se a tela Apps estiver sem internet (erro "TV Plus ... check your network") o 12345 e ignorado; (2) controle slim sem numeros: usar API de controle remoto para enviar KEY_1..KEY_5; (3) se o foco estiver em "Entrar" abre login da conta Samsung - fechar com Return, NAO digitar credenciais.
- Verificar: GET :8001/api/v2/ -> device.developerMode "1", developerIP.

## Sideload Jellyfin
- Mac sem Docker Desktop: brew install colima && colima start --cpu 2 --memory 2
- docker pull georift/install-jellyfin-tizen ; docker run --rm georift/install-jellyfin-tizen TV_IP (16 s, pacote AprZAARz4r.Jellyfin, versao 0.1.0 do wgt)
- Imagem e amd64; roda em Mac ARM via emulacao (aviso de plataforma, inofensivo).
- GET :8001/api/v2/applications/AprZAARz4r.Jellyfin -> {"running":true,"visible":true}

## Limites do modo dev
- sdb capability: sdbd_rootperm disabled, appcmd_support disabled, shell interativo "closed".
- `sdb uninstall <pkg>` e `0 vd_appuninstall` recusados para apps pre-carregados (testado RTE Player). So remove apps assinados por nos.
- `sdb shell "0 applist"` funciona (276 entradas).

## DNS anti-anuncio (AdGuard 94.140.14.14) - verificado com dig
- Bloqueia: samsungads.com, config.samsungads.com, samsungacr.com, log-config.samsungacr.com (ads + ACR).
- Libera: www.samsungotn.net (firmware), api.samsungosp.com (conta).
- Caminho: Configuracoes > Geral > Rede > Status da rede > Configuracoes de IP > Config. DNS > Inserir manualmente.
- Input de IP: 4 campos; ao completar 3 digitos o campo AVANCA SOZINHO. Nao mandar KEY_RIGHT apos 3 digitos (gerou 94.140.0.4). Regra: 2 digitos -> KEY_RIGHT; 3 digitos -> nada.

## DNS aplicado (2026-10-31)
- Sequencia que funcionou com campo zerado: KEY_9 KEY_4 KEY_RIGHT KEY_1 KEY_4 KEY_0 (auto-avanca) KEY_1 KEY_4 KEY_RIGHT KEY_1 KEY_4 -> 94.140.14.14
- Salvar: KEY_ENTER no campo DNS, depois KEY_DOWN x2 ate o botao OK da tela "Configuracoes de IP", KEY_ENTER. TV volta para "Status da rede".
- Navegacao usada: KEY_MENU (Configuracoes) -> foco em Geral -> KEY_ENTER x3 (Geral > Rede > Status da rede) -> Configuracoes de IP -> Config. DNS -> Inserir manualmente.
- Apos salvar o DNS a TV voltou para "Status da rede"; API :8001 continuou respondendo (ip TV_IP, wired).
- ed.apps.launch NAO funciona com o menu Configuracoes aberto (YouTube ficou running:false). Fechar com KEY_RETURN x3 + KEY_HOME antes de lancar; Jellyfin abriu (running:true) em seguida.

## Configurar servidor no app Jellyfin (via API)
- Tela "Select Server" -> foco em "Add Server" -> KEY_ENTER -> KEY_ENTER (abre IME no campo) -> texto via
  {"method":"ms.remote.control","params":{"Cmd":"<base64 do texto>","DataOfCmd":"base64","TypeOfRemote":"SendInputString"}} + {"TypeOfRemote":"SendInputEnd"}
- Endereco digitado: JELLYFIN_HOST:8096 (tvkeys.py aceita token TEXT:<string>).

## Smart Hub pela API (Tizen 5.0 / 2019)
- KEY_MENU NAO abre Configuracoes nesse modelo: abre a Home com foco em Apps. Engrenagem Configuracoes = ponta esquerda da barra (KEY_LEFT ate "Notificacoes", 1 KEY_RIGHT = Configuracoes, KEY_ENTER abre o menu completo com foco em Picture).
- Menu completo: Picture, Sound, Broadcasting (desabilitado sem antena -> pula), General, Support. De Picture, 2x KEY_DOWN = General quando Broadcasting esta desabilitado.
- General: Network, External Device Manager, Eco Solution, System Manager, Accessibility, Smart Features (6x KEY_DOWN de Network).
- Smart Features: Autorun Smart Hub (estava ON -> KEY_ENTER alterna), Autorun Last App (OFF).

## Jellyfin via API (feito com API key, Dashboard > API Keys)
- Custom CSS: GET/POST /System/Configuration/branding {CustomCss, SplashscreenEnabled:false} -> 204.
- Prefs por usuario: GET/POST /DisplayPreferences/usersettings?userId=<id>&client=emby ; CustomPrefs: enableBackdrops/ThemeSongs/ThemeVideos=false, screensaver=none, enableBlurhash=false, homesection0..6 (smalllibrarytiles, resume, nextup, none...).
- Servidor ja usa VAAPI (EnableHardwareEncoding true). O app da TV precisa ser reaberto para carregar CSS/prefs.
- Script: scripts/jellyfin-apply.sh (JF_URL + JF_KEY).
