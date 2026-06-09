import cv2
import mediapipe as mp
import time
import random

# ====================================================================
# CARREGAMENTO DE IMAGENS EXTERNAS
# ====================================================================
img_joia = cv2.imread('joia.jpeg')
img_triste = cv2.imread('triste.jpeg')
img_kabom = cv2.imread('kabom.jpeg')

# Inicializar o MediaPipe CONFIGURADO PARA ATÉ 2 MÃOS
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.65)
mp_draw = mp.solutions.drawing_utils

# PALETA DE CORES HUD (Padrão BGR)
COR_BG_HUD    = (30, 30, 30)       
COR_TEXTO     = (240, 240, 240)    
COR_SUCESSO   = (46, 204, 113)     
COR_ALERTA    = (50, 50, 240)

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
# FUNÇÕES DE DETECÇÃO DE GESTOS
# ====================================================================
def analyze_hand_gestures(results):
    joia_detected = False
    triste_detected = False
    
    if not results.multi_hand_landmarks:
        return False, False

    for hand_landmarks in results.multi_hand_landmarks:
        tip_th = hand_landmarks.landmark[4]  
        tip_in = hand_landmarks.landmark[8]  
        tip_mi = hand_landmarks.landmark[12] 
        
        pip_th = hand_landmarks.landmark[3]
        pip_in = hand_landmarks.landmark[6]
        pip_mi = hand_landmarks.landmark[10]
        pip_an = hand_landmarks.landmark[14]
        pip_pi = hand_landmarks.landmark[18]
        
        th_up = tip_th.y < pip_th.y - 0.02
        th_down = tip_th.y > pip_th.y + 0.02
        
        in_open = tip_in.y < pip_in.y - 0.02
        mi_open = tip_mi.y < pip_mi.y - 0.02
        an_open = hand_landmarks.landmark[16].y < pip_an.y - 0.02
        pi_open = hand_landmarks.landmark[20].y < pip_pi.y - 0.02
        
        four_closed = (not in_open) and (not mi_open) and (not an_open) and (not pi_open)
        
        # 1. Sinal de Jóia (Polegar para cima, resto fechado)
        if th_up and four_closed:
            joia_detected = True
        # 2. Jóia ao Contrário (Polegar para baixo, resto fechado)
        elif th_down and four_closed:
            triste_detected = True
    
    return joia_detected, triste_detected

# ====================================================================
# FUNÇÕES DE RENDERIZAÇÃO GRÁFICA DO HUD
# ====================================================================
def draw_hud_panel(frame, x1, y1, x2, y2, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), COR_BG_HUD, -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), 2)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_fullscreen_fallback(frame, cor_bg):
    frame[:] = cor_bg

# Inicializar Câmera e Fullscreen
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

NOME_JANELA = "Simulador de Gases Ideais"
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
exploded_state = False
explosion_timer = 0
pressure = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.resize(frame, (screen_w, screen_h))
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    state_joia, state_triste = analyze_hand_gestures(results)

    # Processamento analógico das barras (Apenas se o simulador estiver ativo e sem interrupções de gestos)
    if results.multi_hand_landmarks and not exploded_state and not (state_joia or state_triste):
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
            # MÃO ESQUERDA -> TEMPERATURA
            else:
                current_temp = int(((dist_pinca - min_pinca) / (max_pinca - min_pinca)) * 95 + 5)
                current_temp = max(5, min(current_temp, 100))
                cv2.line(frame, (pol_x, pol_y), (ind_x, ind_y), (255, 255, 100), 3, lineType=cv2.LINE_AA)
                cv2.putText(frame, "TEMP", (ind_x - 20, ind_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 2)

    if exploded_state:
        tempo_decorrido = time.time() - explosion_timer
        if tempo_decorrido > 3.0: 
            exploded_state = False
            current_volume = 450
            current_temp = 40
    else:
        pressure = int((current_temp / current_volume) * 2500)
        if pressure >= 450:
            exploded_state = True
            explosion_timer = time.time()

    # ====================================================================
    # MÁQUINA DE RENDERIZAÇÃO E PRIORIDADES VISUAIS
    # ====================================================================
    
    # PRIORIDADE 1: SISTEMA DE EXPLOSÃO (Tela Branca + Fade-in Reverso + Legenda)
    if exploded_state:
        frame[:] = 255 
        
        if img_kabom is not None:
            img_resized = cv2.resize(img_kabom, (w, h))
            alpha = min(1.0, (time.time() - explosion_timer) / 2.0)
            if alpha > 0:
                cv2.addWeighted(img_resized, alpha, frame, 1.0 - alpha, 0, frame)

        texto_legenda = "O RECIPIENTE EXPLODIU!"
        fonte = cv2.FONT_HERSHEY_SIMPLEX
        escala = 1.3
        espessura = 4
        
        tamanho_texto, _ = cv2.getTextSize(texto_legenda, fonte, escala, espessura)
        texto_x = (w - tamanho_texto[0]) // 2
        texto_y = h - 80
        
        cv2.putText(frame, texto_legenda, (texto_x, texto_y), fonte, escala, (0, 0, 0), espessura + 3, lineType=cv2.LINE_AA)
        cv2.putText(frame, texto_legenda, (texto_x, texto_y), fonte, escala, (0, 0, 255), espessura, lineType=cv2.LINE_AA)

    # PRIORIDADE 2: OVERLAY DE IMAGEM DO SINAL JÓIA
    elif state_joia:
        if img_joia is not None: frame[:] = cv2.resize(img_joia, (w, h))
        else: draw_fullscreen_fallback(frame, (100, 200, 100))

    # PRIORIDADE 3: OVERLAY DE IMAGEM DO SINAL TRISTE (Jóia Invertido)
    elif state_triste:
        if img_triste is not None: frame[:] = cv2.resize(img_triste, (w, h))
        else: draw_fullscreen_fallback(frame, (180, 100, 40))

    # RENDERIZAÇÃO PADRÃO: SIMULADOR E HUD
    else:
        box_w = current_volume
        box_h = 320
        cx, cy = w // 2, h // 2 + 50
        x_min, x_max = cx - box_w // 2, cx + box_w // 2
        y_min, y_max = cy - box_h // 2, cy + box_h // 2
        
        # Altera a cor da borda baseado na criticidade da pressão (acima de 280 fica vermelho)
        cor_borda = COR_ALERTA if pressure >= 280 else (230, 230, 230)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (20, 20, 20), -1)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), cor_borda, 4)
        
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

        # Painéis HUD informativos
        draw_hud_panel(frame, 40, 40, 420, 200, alpha=0.75)
        cv2.putText(frame, "CONTROLES ATIVOS POR MAO", (55, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 220, 255), 2)
        cv2.putText(frame, f"Esquerda -> Temp (T): {current_temp} K", (55, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 100), 2)
        cv2.putText(frame, f"Direita  -> Volume (V): {current_volume} L", (55, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        
        draw_hud_panel(frame, w // 2 - 150, 40, w // 2 + 150, 120, alpha=0.8)
        cor_p = COR_ALERTA if pressure >= 280 else COR_SUCESSO
        cv2.putText(frame, f"PRESSAO: {pressure} Atm", (w // 2 - 120, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_p, 3)

        if not results.multi_hand_landmarks:
            draw_hud_panel(frame, w//2 - 250, h - 70, w//2 + 250, h - 20, alpha=0.9)
            cv2.putText(frame, "RECIPIENTE EM ESPERA. INSIRA AS MAOS.", (w//2 - 215, h - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)

    cv2.imshow(NOME_JANELA, frame)
    if cv2.waitKey(1) & 0xFF == 27: 
        break

cap.release()
cv2.destroyAllWindows()
