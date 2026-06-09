import cv2
import mediapipe as mp
import serial
import time
import random

# ====================================================================
# CONFIGURAÇÃO DA PORTA SERIAL (Ajuste para a porta do seu Arduino)
# Exemplo no Windows: 'COM3' | Exemplo no Linux/Mac: '/dev/ttyUSB0'
# ====================================================================
PORTA_SERIAL = 'COM3'  
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    print("Arduino conectado com sucesso!")
except Exception as e:
    arduino = None
    print(f"Aviso: Não foi possível conectar ao Arduino na porta {PORTA_SERIAL}.")
    print("O jogo rodará apenas na tela.")

# Inicializar o MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

def count_fingers(hand_landmarks):
    """Conta quais dedos estão levantados."""
    fingers = []
    # Verifica os 4 dedos principais (Indicador, Médio, Anelar, Mínimo)
    # A ponta do dedo (id) deve estar mais alta (valor y menor) que a articulação inferior (id - 2)
    tip_ids = [8, 12, 16, 20]
    for id in tip_ids:
        if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def get_gesture(fingers):
    """Classifica o gesto baseado nos dedos levantados."""
    # fingers = [Indicador, Médio, Anelar, Mínimo]
    up_count = sum(fingers)
    
    if up_count == 0:
        return "pedra"
    elif up_count == 4:
        return "papel"
    elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
        return "tesoura"
    elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
        return "3"
    
    return "desconhecido"

# Inicializar Câmera
cap = cv2.VideoCapture(0)

# Variáveis de Controle de Estado
state = "WAITING"
countdown_start = 0
computer_choice = ""
user_choice = ""
result_text = ""
result_time = 0

print("Pressione 'ESC' para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Espelhar o frame para agir como um espelho e converter cores
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    gesture = "nenhum"

    # Desenhar os marcos da mão e detectar gesto
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            fingers = count_fingers(hand_landmarks)
            gesture = get_gesture(fingers)
            cv2.putText(frame, f"Gesto: {gesture}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # ==========================
    # MÁQUINA DE ESTADOS DO JOGO
    # ==========================
    
    if state == "WAITING":
        cv2.putText(frame, "Faca o sinal de '3' para comecar!", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        if gesture == "3":
            state = "COUNTDOWN"
            countdown_start = time.time()

    elif state == "COUNTDOWN":
        elapsed = time.time() - countdown_start
        if elapsed < 1:
            cv2.putText(frame, "3", (280, 250), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
        elif elapsed < 2:
            cv2.putText(frame, "2", (280, 250), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
        elif elapsed < 3:
            cv2.putText(frame, "1", (280, 250), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
        else:
            state = "PLAY"
            # O Computador escolhe
            computer_choice = random.choice(["pedra", "papel", "tesoura"])
            # Enviar para o Arduino
            if arduino:
                arduino.write((computer_choice + '\n').encode('utf-8'))
                
    elif state == "PLAY":
        cv2.putText(frame, "FACA SUA JOGADA AGORA!", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 3)
        # O código espera reconhecer pedra, papel ou tesoura após a contagem
        if gesture in ["pedra", "papel", "tesoura"]:
            user_choice = gesture
            
            # Lógica de vitória
            if user_choice == computer_choice:
                result_text = "Empate!"
            elif (user_choice == "pedra" and computer_choice == "tesoura") or \
                 (user_choice == "papel" and computer_choice == "pedra") or \
                 (user_choice == "tesoura" and computer_choice == "papel"):
                result_text = "Você Venceu!"
            else:
                result_text = "Computador Venceu!"
                
            state = "RESULT"
            result_time = time.time()

    elif state == "RESULT":
        cv2.putText(frame, f"PC: {computer_choice.upper()} vs VOCE: {user_choice.upper()}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.putText(frame, result_text, (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)

        # Mostra o resultado por 4 segundos antes de zerar
        if time.time() - result_time > 4:
            if arduino:
                arduino.write(b'zerar\n')
            state = "WAITING"

    # Exibir a janela
    cv2.imshow("Pedra, Papel, Tesoura x Arduino", frame)

    # Sair do loop ao pressionar a tecla 'ESC' (código 27)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Limpar recursos
cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()