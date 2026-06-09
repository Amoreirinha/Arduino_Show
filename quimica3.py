import cv2
import mediapipe as mp
import time
import random

# ====================================================================
# CARREGAMENTO DE IMAGENS EXTERNAS
# ====================================================================
img_joia = cv2.imread('joia.jpeg')
img_bravo = cv2.imread('bravo.jpeg')
img_triste = cv2.imread('triste.jpeg')
img_kabom = cv2.imread('kabom.jpeg')

# Inicializar o MediaPipe CONFIGURADO PARA ATÉ 2 MÃOS
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.65)
mp_draw = mp.solutions.drawing_utils

# PALETA DE CORES DO BMO (Padrão BGR)
COR_BMO_CORPO       = (170, 195, 115)   
COR_BMO_TELA        = (195, 240, 200)   
COR_BMO_TELA_ALERT  = (70, 70, 240)     
COR_BMO_FACE        = (65, 60, 45)      
COR_BMO_BOCHECHA    = (160, 170, 255)   

COR_BG_HUD    = (30, 30, 30)       
COR_TEXTO     = (240, 240, 240)    
COR_SUCESSO   = (46, 204, 113)     

# ====================================================================
# CONFIGURAÇÃO DA SIMULAÇÃO DE GASES
# ====================================================================
NUM_PARTICULAS = 35
particulas = []

for _ in range(NUM_PARTICULAS):
    particulas.append({
        'x': random.randint(300, 900),
        'y': random.randint(300, 600),
        'vx': random.choice([-1, 1]) * random.uniform(1.5, 3.0),
        'vy': random.choice([-1, 1]) * random.uniform(1.5, 3.0)
    })

# ====================================================================
# FUNÇÕES DE DETECÇÃO DE GESTOS AVANÇADOS
# ====================================================================
def is_finger_open(tip_y, pip_y):
    return tip_y < pip_y - 0.02

def analyze_hand_gestures(results):
    """Analisa as mãos na tela e retorna True/False para os estados solicitados."""
    joia_detected = False
    triste_detected = False
    fist_count = 0
    
    if not results.multi_hand_landmarks:
        return False, False, False

    for hand_landmarks in results.multi_hand_landmarks:
        # Marcos das pontas e articulações dos dedos
        tip_th = hand_landmarks.landmark[4]  
        tip_in = hand_landmarks.landmark[8]  
        tip_mi = hand_landmarks.landmark[12] 
        
        pip_th = hand_landmarks.landmark[3]
        pip_in = hand_landmarks.landmark[6]
        pip_mi = hand_landmarks.landmark[10]
        pip_an = hand_landmarks.landmark[14]
        pip_pi = hand_landmarks.landmark[18]
        
        # Leituras verticais de orientação (Y cresce para baixo na tela)
        th_up = tip_th.y < pip_th.y - 0.02
        th_down = tip_th.y > pip_th.y + 0.02
        
        in_open = tip_in.y < pip_in.y - 0.02
        mi_open = tip_mi.y < pip_mi.y - 0.02
        an_open = hand_landmarks.landmark[16].y < pip_an.y - 0.02
        pi_open = hand_landmarks.landmark[20].y < pip_pi.y - 0.02
        
        # Quatro dedos principais fechados
        four_closed = (not in_open) and (not mi_open) and (not an_open) and (not pi_open)
        
        # 1. Sinal de Jóia (Polegar para cima, resto fechado)
        if th_up and four_closed:
            joia_detected = True
        # 2. Jóia ao Contrário (Polegar para baixo, resto fechado)
        elif th_down and four_closed:
            triste_detected = True
        # 3. Contagem de punhos (Todos os dedos fechados)
        elif four_closed and (not th_up) and (not th_down):
            fist_count += 1

    # Bravo só ativa se as DUAS mãos estiverem fechadas em punho simultaneamente
    bravo_detected = (len(results.multi_hand_landmarks) == 2) and (fist_count == 2)
    
    return joia_detected, triste_detected, bravo_detected

# ====================================================================
# FUNÇÕES DE RENDERIZAÇÃO GRÁFICA DO HUD
# ====================================================================
def draw_hud_panel(frame, x1, y1, x2, y2, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), COR_BG_HUD, -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), 2)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_fullscreen_fallback(frame, cor_bg):
    """Gera uma tela limpa caso o arquivo de imagem correspondente falte."""
    frame[:] = cor_bg

def draw_bmo(frame, x, y, w_size=210, h_size=250, mood="neutral"):
    cv2.rectangle(frame, (x, y), (x + w_size, y + h_size), COR_BMO_CORPO, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x + w_size, y + h_size), (130, 155, 85), 3, lineType=cv2.LINE_AA)
    
    scale = w_size / 210.0
    th_margin = int(15 * scale)
    tw = w_size - (th_margin * 2)
    th = h_size - int(110 * scale)
    
    cor_tela = COR_BMO_TELA_ALERT if mood in ["panic", "exploded"] else COR_BMO_TELA
    tx1, ty1 = x + th_margin, y + th_margin
    tx2, ty2 = x + th_margin + tw, y + th_margin + th
    cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), cor_tela, -1, lineType=cv2.LINE_AA)
    
    if w_size == 210:
        cv2.rectangle(frame, (x + 30, y + 180), (x + 60, y + 195), (40, 40, 40), -1)
        cv2.rectangle(frame, (x + 40, y + 170), (x + 50, y + 205), (40, 40, 40), -1)
        cv2.circle(frame, (x + 160, y + 185), 14, (220, 100, 50), -1, lineType=cv2.LINE_AA) 
        cv2.circle(frame, (x + 120, y + 210), 10, (60, 60, 230), -1, lineType=cv2.LINE_AA)

    cx = tx1 + (tw // 2)
    cy = ty1 + (th // 2)
    eye_size = int(8 * scale)
    mouth_w = int(15 * scale)
    mouth_h = int(10 * scale)
    
    if mood == "happy":
        cv2.circle(frame, (cx - int(40*scale), cy - int(15*scale)), eye_size, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + int(40*scale), cy - int(15*scale)), eye_size, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + int(10*scale)), (mouth_w, mouth_h), 0, 0, 180, COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
    elif mood == "neutral":
        cv2.circle(frame, (cx - int(40*scale), cy - int(15*scale)), eye_size, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + int(40*scale), cy - int(15*scale)), eye_size, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + int(10*scale)), (mouth_w, mouth_h), 0, 0, 180, COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
    elif mood == "panic":
        cv2.line(frame, (cx - int(45*scale), cy - int(30*scale)), (cx - int(20*scale), cy - int(25*scale)), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + int(45*scale), cy - int(30*scale)), (cx + int(20*scale), cy - int(25*scale)), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - int(35*scale), cy - int(10*scale)), int(9*scale), COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + int(35*scale), cy - int(10*scale)), int(9*scale), COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx, cy + int(20*scale)), int(12*scale), COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
    elif mood == "exploded":
        cv2.line(frame, (cx - int(45*scale), cy - int(25*scale)), (cx - int(25*scale), cy - int(5*scale)), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - int(25*scale), cy - int(25*scale)), (cx - int(45*scale), cy - int(5*scale)), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + int(25*scale), cy - int(25*scale)), (cx + int(45*scale), cy - int(5*scale)), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + int(45*scale), cy - int(25*scale)), (cx + int(25*scale), cy - int(5*scale)), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - int(25*scale), cy + int(20*scale)), (cx + int(25*scale), cy + int(20*scale)), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)

# Inicializar Câmera e Fullscreen
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

NOME_JANELA = "BMO - Simulador de Gases Ideais"
cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(NOME_JANELA, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

screen_w, screen_h = 1280, 720
for _ in range(10):
    ret, frame = cap.read()
    if ret:
        cv2.imshow(NOME_JANELA, frame)
        cv2.waitKey(1)
        rect = cv2.getWindowImageRect(NOME_JANELA)
        if rect[2] > 0 and rect[3] > 0:
            screen_w, screen_h = rect[2], rect[3]
            break

# Estados físicos iniciais
current_volume = 450
current_temp = 40
bot_mood = "neutral"
exploded_state = False
explosion_timer = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.resize(frame, (screen_w, screen_h))
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Coletar estados dos novos gestos
    state_joia, state_triste, state_bravo = analyze_hand_gestures(results)

    # Processamento analógico das barras (Apenas se o simulador estiver ativo e sem interrupções de gestos)
    if results.multi_hand_landmarks and not exploded_state and not (state_joia or state_triste or state_bravo):
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            punho_x = hand_landmarks.landmark[0].x
            polegar = hand_landmarks.landmark[4]
            indicador = hand_landmarks.landmark[8]
            
            pol_x, pol_y = int(polegar.x * w), int(polegar.y * h)
            ind_x, ind_y = int(indicador.x * w), int(indicador.y * h)
            
            dist_pinca = ((pol_x - ind_x)**2 + (pol_y - ind_y)**2)**0.5
            min_pinca, max_pinca = 25, 150
            
            # MÃO DIREITA -> VOLUME
            if punho_x > 0.5:
                current_volume = int(((dist_pinca - min_pinca) / (max_pinca - min_pinca)) * 550 + 200)
                current_volume = max(200, min(current_volume, 750))
                cv2.line(frame, (pol_x, pol_y), (ind_x, ind_y), (100, 255, 100), 3, lineType=cv2.LINE_AA)
                cv2.putText(frame, "VOLUME", (ind_x - 30, ind_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 2)
                
            # MÃO ESQUERDA -> TEMPERATURE
            else:
                current_temp = int(((dist_pinca - min_pinca) / (max_pinca - min_pinca)) * 95 + 5)
                current_temp = max(5, min(current_temp, 100))
                cv2.line(frame, (pol_x, pol_y), (ind_x, ind_y), (255, 255, 100), 3, lineType=cv2.LINE_AA)
                cv2.putText(frame, "TEMP", (ind_x - 20, ind_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 2)

    # Máquina lógica de pressão física
    if exploded_state:
        bot_mood = "exploded"
        tempo_decorrido = time.time() - explosion_timer
        if tempo_decorrido > 3.0: # Duração da tela de explosão
            exploded_state = False
            current_volume = 450
            current_temp = 40
    else:
        pressure = int((current_temp / current_volume) * 2500)
        if pressure < 120: bot_mood = "happy"
        elif pressure < 280: bot_mood = "neutral"
        else: bot_mood = "panic"

        if pressure >= 450:
            exploded_state = True
            explosion_timer = time.time()

    # ====================================================================
    # MÁQUINA DE RENDERIZAÇÃO E PRIORIDADES VISUAIS
    # ====================================================================
    
    # PRIORIDADE 1: SISTEMA DE EXPLOSÃO (Tela Branca + Fadeout Kabom)
    if exploded_state:
        frame[:] = 255 # Deixa a tela inteira em branco puro
        
        if img_kabom is not None:
            img_resized = cv2.resize(img_kabom, (w, h))
            # O fadeout acontece reduzindo a opacidade linearmente ao longo de 2 segundos
            alpha = max(0.0, 1.0 - ((time.time() - explosion_timer) / 2.0))
            if alpha > 0:
                cv2.addWeighted(img_resized, alpha, frame, 1.0 - alpha, 0, frame)

    # PRIORIDADE 2: OVERLAY DE IMAGEM DO SINAL BRAVO (Punho Duplo)
    elif state_bravo:
        if img_bravo is not None: frame[:] = cv2.resize(img_bravo, (w, h))
        else: draw_fullscreen_fallback(frame, (40, 40, 180)) # Vermelho se faltar arquivo

    # PRIORIDADE 3: OVERLAY DE IMAGEM DO SINAL JÓIA
    elif state_joia:
        if img_joia is not None: frame[:] = cv2.resize(img_joia, (w, h))
        else: draw_fullscreen_fallback(frame, (100, 200, 100)) # Verde se faltar arquivo

    # PRIORIDADE 4: OVERLAY DE IMAGEM DO SINAL TRISTE (Jóia Invertido)
    elif state_triste:
        if img_triste is not None: frame[:] = cv2.resize(img_triste, (w, h))
        else: draw_fullscreen_fallback(frame, (180, 100, 40)) # Azul se faltar arquivo

    # RENDERIZAÇÃO PADRÃO: SIMULADOR E HUD
    else:
        # Container de Gás
        box_w = current_volume
        box_h = 320
        cx, cy = w // 2, h // 2 + 120
        x_min, x_max = cx - box_w // 2, cx + box_w // 2
        y_min, y_max = cy - box_h // 2, cy + box_h // 2
        
        cor_borda = (50, 50, 240) if bot_mood == "panic" else (230, 230, 230)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (20, 20, 20), -1)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), cor_borda, 4)
        
        # Partículas de gás
        r_part = int((current_temp / 100) * 255)
        b_part = int((1 - (current_temp / 100)) * 255)
        cor_particula = (b_part, 100, r_part)
        velocidade_mult = current_temp * 0.15
        
        for p in particulas:
            p['x'] += p['vx'] * velocidade_mult
            p['y'] += p['vy'] * velocidade_mult
            if p['x'] < x_min + 10: p['x'] = x_min + 12; p['vx'] *= -1
            elif p['x'] > x_max - 10: p['x'] = x_max - 12; p['vx'] *= -1
            if p['y'] < y_min + 10: p['y'] = y_min + 12; p['vy'] *= -1
            elif p['y'] > y_max - 10: p['y'] = y_max - 12; p['vy'] *= -1
            cv2.circle(frame, (int(p['x']), int(p['y'])), 7, cor_particula, -1, lineType=cv2.LINE_AA)

        # Interfaces HUD laterais e superiores
        draw_hud_panel(frame, 40, 40, 420, 200, alpha=0.75)
        cv2.putText(frame, "CONTROLES ATIVOS POR MAO", (55, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 220, 255), 2)
        cv2.putText(frame, f"Esquerda -> Temp (T): {current_temp} K", (55, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 100), 2)
        cv2.putText(frame, f"Direita  -> Volume (V): {current_volume} L", (55, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        
        draw_hud_panel(frame, w // 2 - 150, 40, w // 2 + 150, 120, alpha=0.8)
        cor_p = (50, 50, 255) if bot_mood == "panic" else COR_SUCESSO
        cv2.putText(frame, f"PRESSAO: {pressure} Atm", (w // 2 - 120, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_p, 3)

        if not results.multi_hand_landmarks:
            draw_hud_panel(frame, w//2 - 250, h - 70, w//2 + 250, h - 20, alpha=0.9)
            cv2.putText(frame, "RECIPIENTE EM ESPERA. INSIRA AS MAOS.", (w//2 - 215, h - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)

        # Renderização do HUD clássico do BMO no canto superior direito
        draw_bmo(frame, w - 260, 40, mood=bot_mood)

    cv2.imshow(NOME_JANELA, frame)
    if cv2.waitKey(1) & 0xFF == 27: # Pressione ESC para fechar
        break

cap.release()
cv2.destroyAllWindows()
