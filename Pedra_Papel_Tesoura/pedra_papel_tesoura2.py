import cv2
import mediapipe as mp
import serial
import time
import random

# ====================================================================
# CONFIGURAÇÃO DA PORTA SERIAL (Ajuste para a porta do seu Arduino)
# ====================================================================
PORTA_SERIAL = 'COM3'  
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    print("Arduino conectado com sucesso!")
except Exception as e:
    arduino = None
    print(f"Aviso: Não foi possível conectar ao Arduino na porta {PORTA_SERIAL}.")

# Inicializar o MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# PALETA DE CORES DO BMO (Padrão BGR para o OpenCV)
COR_BMO_CORPO       = (170, 195, 115)   # Verde-azulado do BMO
COR_BMO_TELA        = (195, 240, 200)   # Tela verde-clara normal
COR_BMO_TELA_RAIVA  = (70, 70, 240)     # Tela VERMELHA de pura raiva
COR_BMO_FACE        = (65, 60, 45)      # Cor escura para as feições
COR_BMO_BOCHECHA    = (160, 170, 255)   # Rosa para as bochechas felizes

COR_BG_HUD    = (30, 30, 30)       # Cinza Escuro para painéis HUD
COR_TEXTO     = (240, 240, 240)    # Branco suave
COR_SUCESSO   = (46, 204, 113)     # Verde Vitória
COR_PERDA     = (52, 73, 94)       # Vermelho/Coral derrota
COR_ALERTA    = (230, 126, 34)     # Laranja Contagem

def count_fingers(hand_landmarks):
    fingers = []
    tip_ids = [8, 12, 16, 20] # Indicador, Médio, Anelar, Mínimo
    for id in tip_ids:
        if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def get_gesture(fingers, hand_landmarks):
    up_count = sum(fingers)
    
    # 1. Se apenas o dedo do Meio estiver levantado (Dedos: [0, 1, 0, 0])
    if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
        return "dedo_meio"
        
    # 2. Se os 4 dedos principais estão fechados, pode ser Pedra ou Joinha
    if up_count == 0:
        if hand_landmarks.landmark[4].y < hand_landmarks.landmark[9].y:
            return "joia"
        return "pedra"
    elif up_count == 4:
        return "papel"
    elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
        return "tesoura"
    elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
        return "3"
    return "desconhecido"

def draw_hud_panel(frame, x1, y1, x2, y2, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), COR_BG_HUD, -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), 2)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_bmo(frame, x, y, mood="neutral"):
    """Desenha o BMO ampliado na tela com suporte a expressões e mudança de cor."""
    # Corpo do BMO
    cv2.rectangle(frame, (x, y), (x + 210, y + 250), COR_BMO_CORPO, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x + 210, y + 250), (130, 155, 85), 3, lineType=cv2.LINE_AA)
    
    # Seleção de Cor da Tela baseada no humor
    cor_tela_atual = COR_BMO_TELA_RAIVA if mood == "irritated" else COR_BMO_TELA
    
    # Tela do BMO
    cv2.rectangle(frame, (x + 15, y + 15), (x + 195, y + 140), cor_tela_atual, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x + 15, y + 15), (x + 195, y + 140), (150, 190, 155) if mood != "irritated" else (40, 40, 180), 2, lineType=cv2.LINE_AA)
    
    # Botões Físicos do BMO
    cv2.rectangle(frame, (x + 30, y + 180), (x + 60, y + 195), (40, 40, 40), -1)
    cv2.rectangle(frame, (x + 40, y + 170), (x + 50, y + 205), (40, 40, 40), -1)
    cv2.circle(frame, (x + 160, y + 185), 14, (220, 100, 50), -1, lineType=cv2.LINE_AA) 
    cv2.circle(frame, (x + 120, y + 210), 10, (60, 60, 230), -1, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (x + 30, y + 225), (x + 55, y + 230), (40, 40, 40), -1)
    cv2.rectangle(frame, (x + 65, y + 225), (x + 90, y + 230), (40, 40, 40), -1)

    cx, cy = x + 105, y + 77 # Centro da tela
    
    if mood == "neutral":
        cv2.circle(frame, (cx - 40, cy - 15), 8, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 40, cy - 15), 8, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + 10), (15, 10), 0, 0, 180, COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        
    elif mood == "thinking":
        cv2.line(frame, (cx - 50, cy - 15), (cx - 25, cy - 15), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 25, cy - 15), (cx + 50, cy - 15), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx, cy + 15), 6, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        
    elif mood == "happy":
        cv2.ellipse(frame, (cx - 40, cy - 10), (14, 12), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx + 40, cy - 10), (14, 12), 0, 180, 360, COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - 55, cy + 15), 10, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 55, cy + 15), 10, COR_BMO_BOCHECHA, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + 10), (22, 18), 0, 0, 180, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        
    elif mood == "sad":
        cv2.line(frame, (cx - 55, cy - 30), (cx - 25, cy - 20), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 55, cy - 30), (cx + 25, cy - 20), COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - 40, cy - 10), 9, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 40, cy - 10), 9, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + 25), (18, 12), 0, 180, 360, COR_BMO_FACE, 3, lineType=cv2.LINE_AA)
        
    elif mood == "irritated":
        # Sobrancelhas super inclinadas de raiva extrema (V de vingança)
        cv2.line(frame, (cx - 50, cy - 32), (cx - 20, cy - 18), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + 50, cy - 32), (cx + 20, cy - 18), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)
        # Olhos espremidos de fúria
        cv2.circle(frame, (cx - 35, cy - 10), 7, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + 35, cy - 10), 7, COR_BMO_FACE, -1, lineType=cv2.LINE_AA)
        # Boca reta e tensa de insatisfação
        cv2.line(frame, (cx - 30, cy + 20), (cx + 30, cy + 20), COR_BMO_FACE, 4, lineType=cv2.LINE_AA)

# Inicializar Câmera
cap = cv2.VideoCapture(0)

# CONFIGURAÇÃO DE TELA CHEIA (FULLSCREEN)
NOME_JANELA = "Pedra, Papel, Tesoura x BMO Arduino"
cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(NOME_JANELA, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

state = "WAITING"
countdown_start = 0
computer_choice = ""
user_choice = ""
result_text = ""
result_time = 0
bot_mood = "neutral"

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    gesture = "nenhum"

    # Processar Mão
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                mp_draw.DrawingSpec(color=(170, 195, 115), thickness=2)
            )
            fingers = count_fingers(hand_landmarks)
            gesture = get_gesture(fingers, hand_landmarks)

    # ==========================
    # MÁQUINA DE ESTADOS DO JOGO
    # ==========================
    
    if state == "WAITING":
        bot_mood = "neutral"
        draw_hud_panel(frame, 20, h - 70, w - 20, h - 20)
        cv2.putText(frame, "Faca o sinal de '3' para iniciar o jogo!", (40, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COR_TEXTO, 2, cv2.LINE_AA)
        
        if gesture == "3":
            state = "COUNTDOWN"
            countdown_start = time.time()

    elif state == "COUNTDOWN":
        bot_mood = "thinking"
        elapsed = time.time() - countdown_start
        
        draw_hud_panel(frame, w//2 - 60, h//2 - 70, w//2 + 60, h//2 + 50, alpha=0.4)
        
        if elapsed < 1:
            cv2.putText(frame, "3", (w//2 - 25, h//2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 3, COR_ALERTA, 6, cv2.LINE_AA)
        elif elapsed < 2:
            cv2.putText(frame, "2", (w//2 - 25, h//2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 3, COR_ALERTA, 6, cv2.LINE_AA)
        elif elapsed < 3:
            cv2.putText(frame, "1", (w//2 - 25, h//2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 3, COR_ALERTA, 6, cv2.LINE_AA)
        else:
            state = "PLAY"
            computer_choice = random.choice(["pedra", "papel", "tesoura"])
            if arduino:
                arduino.write((computer_choice + '\n').encode('utf-8'))
                
    elif state == "PLAY":
        bot_mood = "thinking"
        draw_hud_panel(frame, 30, h//2 - 40, w - 30, h//2 + 30)
        cv2.putText(frame, "MOSTRE SUA JOGADA NA CAMERA!", (55, h//2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COR_ALERTA, 3, cv2.LINE_AA)
        
        if gesture in ["pedra", "papel", "tesoura"]:
            user_choice = gesture
            
            if user_choice == computer_choice:
                result_text = "Empate tecnico!"
                bot_mood = "neutral"
            elif (user_choice == "pedra" and computer_choice == "tesoura") or \
                 (user_choice == "papel" and computer_choice == "pedra") or \
                 (user_choice == "tesoura" and computer_choice == "papel"):
                result_text = "Voce Venceu!"
                bot_mood = "sad"
            else:
                result_text = "BMO Venceu!"
                bot_mood = "happy"
                
            state = "RESULT"
            result_time = time.time()

    elif state == "RESULT":
        draw_hud_panel(frame, 20, 280, w - 260, 400)
        cor_final = COR_SUCESSO if bot_mood == "sad" else (COR_PERDA if bot_mood == "happy" else COR_TEXTO)
        
        cv2.putText(frame, f"Voce: {user_choice.upper()} vs BMO: {computer_choice.upper()}", (40, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COR_TEXTO, 2, cv2.LINE_AA)
        cv2.putText(frame, result_text, (40, 370), cv2.FONT_HERSHEY_SIMPLEX, 1.2, cor_final, 3, cv2.LINE_AA)

        if time.time() - result_time > 4:
            if arduino:
                arduino.write(b'zerar\n')
            state = "WAITING"

    # INTERRUPÇÕES DE INTERAÇÃO POR GESTOS DIRETOS
    if state != "COUNTDOWN" and state != "RESULT":
        if gesture == "joia":
            bot_mood = "happy"
        elif gesture == "dedo_meio":
            bot_mood = "irritated"

    # Painel fixo do sinal atual detectado
    draw_hud_panel(frame, 20, 20, 260, 70, alpha=0.7)
    cv2.putText(frame, f"Sinal: {gesture.upper()}", (35, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COR_SUCESSO, 2, cv2.LINE_AA)

    # Desenhar o BMO no canto superior direito
    draw_bmo(frame, w - 235, 20, mood=bot_mood)

    # Exibir a tela em Modo Fullscreen
    cv2.imshow(NOME_JANELA, frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()