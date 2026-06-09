import cv2
import mediapipe as mp
import time
import random

# Inicializar o MediaPipe CONFIGURADO PARA ATÉ 2 MÃOS
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.65)
mp_draw = mp.solutions.drawing_utils

# PALETA DE CORES DO BMO (Padrão BGR)
COR_BMO_CORPO       = (170, 195, 115)   # Verde-azulado característico
COR_BMO_TELA        = (195, 240, 200)   # Tela verde-clara normal
COR_BMO_TELA_ALERT  = (70, 70, 240)     # Tela VERMELHA de alta pressão
COR_BMO_FACE        = (65, 60, 45)      # Cor escura para as feições (Olhos/Boca)
COR_BMO_BOCHECHA    = (160, 170, 255)   # Rosa claro para as bochechas felizes

COR_BG_HUD    = (30, 30, 30)       # Cinza Escuro para painéis HUD
COR_TEXTO     = (240, 240, 240)    # Branco suave
COR_SUCESSO   = (46, 204, 113)     # Verde Vitória

# ====================================================================
# CONFIGURAÇÃO DA SIMULAÇÃO DE GASES
# ====================================================================
NUM_PARTICULAS = 35
particulas = []

# Inicializar posições e direções aleatórias para as moléculas de gás
for _ in range(NUM_PARTICULAS):
    particulas.append({
        'x': random.randint(300, 900),
        'y': random.randint(300, 600),
        'vx': random.choice([-1, 1]) * random.uniform(1.5, 3.0),
        'vy': random.choice([-1, 1]) * random.uniform(1.5, 3.0)
    })

# ====================================================================
# FUNÇÕES DE DETECÇÃO DE GESTOS (Lógica de Easter Egg)
# ====================================================================
def is_finger_open(tip_y, pip_y):
    """Verifica se o dedo está estendido baseado no landmark y."""
    return tip_y < pip_y - 0.02

def detect_gesture_joia_for_egg(hand_landmarks):
    """Detecta apenas o sinal de 'Jóia' baseado nos landmarks."""
    # Pontas dos dedos
    tip_th = hand_landmarks.landmark[4]  # Polegar
    tip_in = hand_landmarks.landmark[8]  # Indicador
    tip_mi = hand_landmarks.landmark[12] # Médio
    tip_an = hand_landmarks.landmark[16] # Anelar
    tip_pi = hand_landmarks.landmark[20] # Mínimo
    
    # Articulações de referência (pip)
    pip_th = hand_landmarks.landmark[3]
    pip_in = hand_landmarks.landmark[6]
    pip_mi = hand_landmarks.landmark[10]
    pip_an = hand_landmarks.landmark[14]
    pip_pi = hand_landmarks.landmark[18]
    
    # Estado aberto/fechado
    th_open = is_finger_open(tip_th.y, pip_th.y)
    in_open = is_finger_open(tip_in.y, pip_in.y)
    mi_open = is_finger_open(tip_mi.y, pip_mi.y)
    an_open = is_finger_open(tip_an.y, pip_an.y)
    pi_open = is_finger_open(tip_pi.y, pip_pi.y)
    
    joinha = False
    
    # Lógica do JÓIA (Polegar aberto, todos os outros fechados)
    if th_open and not in_open and not mi_open and not an_open and not pi_open:
        joinha = True
        
    return joinha

# ====================================================================
# FUNÇÕES DE RENDERIZAÇÃO GRÁFICA
# ====================================================================
def draw_hud_panel(frame, x1, y1, x2, y2, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), COR_BG_HUD, -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), 2)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_bmo(frame, x, y, w_size=210, h_size=250, mood="neutral"):
    """Desenha o BMO na tela com suporte a expressões corporais e tamanho variável."""
    # 1. Corpo/Hardware do BMO
    cv2.rectangle(frame, (x, y), (x + w_size, y + h_size), COR_BMO_CORPO, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x + w_size, y + h_size), (130, 155, 85), 3, lineType=cv2.LINE_AA)
    
    # Ajuste de proporção para os elementos internos baseados no tamanho
    scale = w_size / 210.0
    th_margin = int(15 * scale)
    tw = w_size - (th_margin * 2)
    th = h_size - int(110 * scale)
    
    # 2. Tela do BMO
    cor_tela = COR_BMO_TELA_ALERT if mood in ["panic", "exploded"] else COR_BMO_TELA
    if mood == "super_happy": cor_tela = COR_BMO_TELA
    
    tx1, ty1 = x + th_margin, y + th_margin
    tx2, ty2 = x + th_margin + tw, y + th_margin + th
    cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), cor_tela, -1, lineType=cv2.LINE_AA)
    
    # 3. Botões do Hardware (Abaixo da tela, só desenha se for tamanho normal)
    if w_size == 210:
        cv2.rectangle(frame, (x + 30, y + 180), (x + 60, y + 195), (40, 40, 40), -1)
        cv2.rectangle(frame, (x + 40, y + 170), (x + 50, y + 205), (40, 40, 40), -1)
        cv2.circle(frame, (x + 160, y + 185), 14, (220, 100, 50), -1, lineType=cv2.LINE_AA) 
        cv2.circle(frame, (x + 120, y + 210), 10, (60, 60, 230), -1, lineType=cv2.LINE_AA)

    # 4. Expressões Faciais na Tela
    cx = tx1 + (tw // 2)
    cy = ty1 + (th // 2)
    eye_size = int(8 * scale)
    mouth_w = int(15 * scale)
    mouth_h = int(10 * scale)
    
    if mood == "super_happy": 
        # Olhos de arco (^ ^) super felizes
        arc_w = int(14 * scale)
        arc_h = int(12 * scale)
        eye_base_y = int(cy - 10 * scale)
        cv2.ellipse(frame, (cx - int(40*scale), eye_base_y), (arc_w, arc_h), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx + int(40*scale), eye_base_y), (arc_w, arc_h), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        
        # Bochechas elípticas rosadas
        cheek_y = int(cy + 15 * scale)
        cheek_x_offset = int(55 * scale)
        cv2.ellipse(frame, (cx - cheek_x_offset, cheek_y), (int(12*scale), int(8*scale)), 0, 0, 360, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx + cheek_x_offset, cheek_y), (int(12*scale), int(8*scale)), 0, 0, 360, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        
        # Bocão aberto feliz (Sorrisão amplo)
        cv2.ellipse(frame, (cx, cy + int(10*scale)), (int(25*scale), int(20*scale)), 0, 0, 180, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)

    elif mood == "happy":
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

# Inicializar Câmera e Modo Fullscreen
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

NOME_JANELA = "BMO - Simulador de Gases Ideais"
cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(NOME_JANELA, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Detectar resolução real do monitor para o ajuste de tela cheia
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

# Valores iniciais padrão
current_volume = 450
current_temp = 40
bot_mood = "neutral"
exploded_state = False
explosion_timer = 0
joinha_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.resize(frame, (screen_w, screen_h))
    frame = cv2.flip(frame, 1)
    
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    joinha_detected = False

    if results.multi_hand_landmarks:
        # 1. Detecção do Easter Egg
        for hand_landmarks in results.multi_hand_landmarks:
            if detect_gesture_joia_for_egg(hand_landmarks):
                joinha_detected = True

        # 2. Processamento do Simulador (Se não houver Easter Egg ativo)
        if not joinha_detected and not exploded_state:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                    mp_draw.DrawingSpec(color=(170, 195, 115), thickness=3)
                )
                
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
                    cv2.circle(frame, (pol_x, pol_y), 6, (0, 180, 0), -1)
                    cv2.circle(frame, (ind_x, ind_y), 6, (0, 180, 0), -1)
                    cv2.putText(frame, "VOLUME", (ind_x - 30, ind_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 2)
                    
                # MÃO ESQUERDA -> TEMPERATURE
                else:
                    current_temp = int(((dist_pinca - min_pinca) / (max_pinca - min_pinca)) * 95 + 5)
                    current_temp = max(5, min(current_temp, 100))
                    
                    cv2.line(frame, (pol_x, pol_y), (ind_x, ind_y), (255, 255, 100), 3, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (pol_x, pol_y), 6, (255, 100, 0), -1)
                    cv2.circle(frame, (ind_x, ind_y), 6, (255, 100, 0), -1)
                    cv2.putText(frame, f"TEMP", (ind_x - 20, ind_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 2)

    # Sistema lógico de Pressão e Física
    if exploded_state:
        bot_mood = "exploded"
        if time.time() - explosion_timer > 3:
            exploded_state = False
            current_volume = 450
            current_temp = 40
    else:
        pressure = int((current_temp / current_volume) * 2500)
        
        if pressure < 120:
            bot_mood = "happy"
        elif pressure < 280:
            bot_mood = "neutral"
        else:
            bot_mood = "panic"

        if pressure >= 450:
            exploded_state = True
            explosion_timer = time.time()

    # ==========================
    # RENDERIZAÇÃO FINAL 
    # ==========================
    
    # --- MODO EASTER EGG JÓIA (Fullscreen) ---
    if joinha_detected:
        draw_hud_panel(frame, 0, 0, w, h, alpha=0.9) # Escurecer fundo
        
        scale_joinha = 3.0
        bw = int(210 * scale_joinha)
        bh = int(250 * scale_joinha)
        cx = (w // 2) - (bw // 2)
        cy = (h // 2) - (bh // 2)
        
        draw_bmo(frame, cx, cy, w_size=bw, h_size=bh, mood="super_happy")
        
    # --- RENDERIZAÇÃO NORMAL (Simulador) ---
    else:
        # 1. Desenhar Container de Gás
        box_w = current_volume
        box_h = 320
        cx, cy = w // 2, h // 2 + 120
        
        x_min, x_max = cx - box_w // 2, cx + box_w // 2
        y_min, y_max = cy - box_h // 2, cy + box_h // 2
        
        cor_borda_container = (50, 50, 240) if bot_mood in ["panic", "exploded"] else (230, 230, 230)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (20, 20, 20), -1)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), cor_borda_container, 4)
        
        r_part = int((current_temp / 100) * 255)
        b_part = int((1 - (current_temp / 100)) * 255)
        cor_particula = (b_part, 100, r_part)

        velocidade_mult = current_temp * 0.15 if not exploded_state else 0
        
        for p in particulas:
            if not exploded_state:
                p['x'] += p['vx'] * velocidade_mult
                p['y'] += p['vy'] * velocidade_mult
                
                if p['x'] < x_min + 10: 
                    p['x'] = x_min + 12
                    p['vx'] *= -1
                elif p['x'] > x_max - 10: 
                    p['x'] = x_max - 12
                    p['vx'] *= -1
                    
                if p['y'] < y_min + 10: 
                    p['y'] = y_min + 12
                    p['vy'] *= -1
                elif p['y'] > y_max - 10: 
                    p['y'] = y_max - 12
                    p['vy'] *= -1

            cv2.circle(frame, (int(p['x']), int(p['y'])), 7, cor_particula, -1, lineType=cv2.LINE_AA)

        # 2. Desenhar Painéis HUD
        draw_hud_panel(frame, 40, 40, 420, 200, alpha=0.75)
        cv2.putText(frame, "CONTROLES ATIVOS POR MAO", (55, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 220, 255), 2)
        cv2.putText(frame, f"Esquerda -> Temp (T): {current_temp} K", (55, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 100), 2)
        cv2.putText(frame, f"Direita  -> Volume (V): {current_volume} L", (55, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        
        draw_hud_panel(frame, w // 2 - 150, 40, w // 2 + 150, 120, alpha=0.8)
        if exploded_state:
            cv2.putText(frame, "RECIPIENTE EXPLODIU!", (w // 2 - 130, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 255), 3)
        else:
            cor_p = (50, 50, 255) if bot_mood == "panic" else COR_SUCESSO
            cv2.putText(frame, f"PRESSAO: {pressure} Atm", (w // 2 - 120, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_p, 3)

        if not results.multi_hand_landmarks:
            draw_hud_panel(frame, w//2 - 250, h - 70, w//2 + 250, h - 20, alpha=0.9)
            cv2.putText(frame, "RECIPIENTE EM ESPERA. INSIRA AS MAOS.", (w//2 - 215, h - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)

        # 3. Desenhar BMO Canto Superior
        draw_bmo(frame, w - 260, 40, mood=bot_mood)

    cv2.imshow(NOME_JANELA, frame)

    if cv2.waitKey(1) & 0xFF == 27: # ESC para fechar
        break

cap.release()
cv2.destroyAllWindows()
