import cv2
import mediapipe as mp
import serial
import time
import random

# ====================================================================
# CONFIGURAÇÃO DA PORTA SERIAL (Arduino)
# ====================================================================
PORTA_SERIAL = 'COM3'  
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    print("Arduino conectado com sucesso!")
except Exception as e:
    arduino = None
    print(f"Aviso: Não foi possível conectar ao Arduino.")

# Inicializar o MediaPipe configurado para 2 mãos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

# PALETA DE CORES DO BMO
COR_BMO_CORPO       = (170, 195, 115)   
COR_BMO_TELA        = (195, 240, 200)   
COR_BMO_TELA_ALERT  = (70, 70, 240)     
COR_BMO_FACE        = (65, 60, 45)      
COR_BMO_BOCHECHA    = (160, 170, 255)   

COR_BG_HUD    = (30, 30, 30)       
COR_TEXTO     = (240, 240, 240)    
COR_SUCESSO   = (46, 204, 113)     
COR_ALERTA    = (52, 73, 94)       

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

def draw_hud_panel(frame, x1, y1, x2, y2, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), COR_BG_HUD, -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), 2)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_bmo(frame, x, y, mood="neutral"):
    cv2.rectangle(frame, (x, y), (x + 210, y + 250), COR_BMO_CORPO, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x + 210, y + 250), (130, 155, 85), 3, lineType=cv2.LINE_AA)
    
    cor_tela = COR_BMO_TELA_ALERT if mood in ["panic", "exploded"] else COR_BMO_TELA
    cv2.rectangle(frame, (x + 15, y + 15), (x + 195, y + 140), cor_tela, -1, lineType=cv2.LINE_AA)
    
    # Botões
    cv2.rectangle(frame, (x + 30, y + 180), (x + 60, y + 195), (40, 40, 40), -1)
    cv2.rectangle(frame, (x + 40, y + 170), (x + 50, y + 205), (40, 40, 40), -1)
    cv2.circle(frame, (x + 160, y + 185), 14, (220, 100, 50), -1, lineType=cv2.LINE_AA) 
    cv2.circle(frame, (x + 120, y + 210), 10, (60, 60, 230), -1, lineType=cv2.LINE_AA)

    cx, cy = x + 105, y + 77
    
    if mood == "happy":
        cv2.ellipse(frame, (cx - 40, cy - 10), (14, 12), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx + 40, cy - 10), (14, 12), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - 55, cy + 15), 10, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 55, cy + 15), 10, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + 10), (22, 18), 0, 0, 180, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
    elif mood == "neutral":
        cv2.circle(frame, (cx - 40, cy - 15), 8, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 40, cy - 15), 8, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + 10), (15, 10), 0, 0, 180, COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
    elif mood == "panic":
        cv2.line(frame, (cx - 45, cy - 30), (cx - 20, cy - 25), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 45, cy - 30), (cx + 20, cy - 25), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - 35, cy - 10), 9, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 35, cy - 10), 9, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx, cy + 20), 12, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
    elif mood == "exploded":
        cv2.line(frame, (cx - 45, cy - 25), (cx - 25, cy - 5), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - 25, cy - 25), (cx - 45, cy - 5), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 25, cy - 25), (cx + 45, cy - 5), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 45, cy - 25), (cx + 25, cy - 5), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - 25, cy + 20), (cx + 25, cy + 20), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)

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

current_volume = 400
current_temp = 50
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

    # Processar detecção de duas mãos simultâneas
    if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
        mão1 = results.multi_hand_landmarks[0]
        mão2 = results.multi_hand_landmarks[1]
        
        # Nós centrais (mão 1 e mão 2) para o cálculo do volume
        h1_x, h1_y = int(mão1.landmark[9].x * w), int(mão1.landmark[9].y * h)
        h2_x, h2_y = int(mão2.landmark[9].x * w), int(mão2.landmark[9].y * h)
        
        cv2.circle(frame, (h1_x, h1_y), 8, (255, 255, 255), -1)
        cv2.circle(frame, (h2_x, h2_y), 8, (255, 255, 255), -1)
        cv2.line(frame, (h1_x, h1_y), (h2_x, h2_y), COR_BMO_CORPO, 2)

        # 1. VOLUME: Distância horizontal entre as duas mãos
        dist_x = abs(h1_x - h2_x)
        current_volume = max(200, min(dist_x, 750)) 
        
        # 2. TEMPERATURA: Controle por Pinça (Distância Polegar [4] e Indicador [8] da Mão 1)
        polegar = mão1.landmark[4]
        indicador = mão1.landmark[8]
        
        pol_x, pol_y = int(polegar.x * w), int(polegar.y * h)
        ind_x, ind_y = int(indicador.x * w), int(indicador.y * h)
        
        # Desenhar indicador visual do ajuste de temperatura (Linha Cyan)
        cv2.line(frame, (pol_x, pol_y), (ind_x, ind_y), (255, 255, 100), 3, lineType=cv2.LINE_AA)
        cv2.circle(frame, (pol_x, pol_y), 6, (0, 165, 255), -1)
        cv2.circle(frame, (ind_x, ind_y), 6, (0, 165, 255), -1)
        
        # Calcular distância euclidiana da pinça em pixels
        dist_pinca = ((pol_x - ind_x)**2 + (pol_y - ind_y)**2)**0.5
        
        # Mapeamento: distância min (~25px colado) até max (~160px aberto) convertido para 5K - 100K
        min_pinca, max_pinca = 25, 160
        current_temp = int(((dist_pinca - min_pinca) / (max_pinca - min_pinca)) * 95 + 5)
        current_temp = max(5, min(current_temp, 100))

    # Sistema de Explosão e Pressão
    if exploded_state:
        bot_mood = "exploded"
        if time.time() - explosion_timer > 3:
            exploded_state = False
            current_volume = 500
            current_temp = 20
    else:
        pressure = int((current_temp / current_volume) * 2500)
        
        if pressure < 120:
            bot_mood = "happy"
        elif pressure < 280:
            bot_mood = "neutral"
        elif pressure < 450:
            bot_mood = "panic"
        else:
            exploded_state = True
            explosion_timer = time.time()
            if arduino:
                arduino.write(b'bip_explosao\n')

    # ====================================================================
    # RENDERIZAÇÃO DO RECIPIENTE DE GÁS
    # ====================================================================
    box_w = current_volume
    box_h = 320
    cx, cy = w // 2, h // 2 + 120
    
    x_min, x_max = cx - box_w // 2, cx + box_w // 2
    y_min, y_max = cy - box_h // 2, cy + box_h // 2
    
    cor_borda_container = (50, 50, 240) if bot_mood in ["panic", "exploded"] else (230, 230, 230)
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (20, 20, 20), -1) 
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), cor_borda_container, 4)
    
    # Cor das partículas (Azul = Frio, Vermelho = Quente)
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

    # ====================================================================
    # INTERFACE HUD
    # ====================================================================
    draw_hud_panel(frame, 40, 40, 380, 200, alpha=0.75)
    cv2.putText(frame, "LEITURA TERMODINAMICA", (55, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
    cv2.putText(frame, f"Temperatura (T): {current_temp} K", (55, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COR_TEXTO, 2)
    cv2.putText(frame, f"Volume (V)     : {current_volume} L", (55, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COR_TEXTO, 2)
    
    draw_hud_panel(frame, w // 2 - 150, 40, w // 2 + 150, 120, alpha=0.8)
    if exploded_state:
        cv2.putText(frame, "RECIPIENTE EXPLODIU!", (w // 2 - 130, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 255), 3)
    else:
        cor_p = (50, 50, 255) if bot_mood == "panic" else COR_SUCESSO
        cv2.putText(frame, f"PRESSAO: {pressure} Atm", (w // 2 - 120, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_p, 3)

    if len(results.multi_hand_landmarks or []) < 2:
        draw_hud_panel(frame, w//2 - 270, h - 70, w//2 + 270, h - 20, alpha=0.9)
        cv2.putText(frame, "COLOQUE AS DUAS MAOS E PINCE PARA CONTROLAR!", (w//2 - 245, h - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)

    draw_bmo(frame, w - 260, 40, mood=bot_mood)

    cv2.imshow(NOME_JANELA, frame)
    if cv2.waitKey(1) & 0xFF == 27: 
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
