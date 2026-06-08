#include <Arduino.h>
#include <Servo.h>

// Definição dos servos
Servo servoDedao;    // Dedo polegar
Servo servoIndicador; // Dedo indicador
Servo servoMedio;    // Dedo médio
Servo servoAnelar;   // Dedo anelar
Servo servoMinimo;   // Dedo mínimo
Servo servoCotovelo; // Cotovelo

// Pinos dos servos
const int pinDedao = 3;
const int pinIndicador = 5;
const int pinMedio = 6;
const int pinAnelar = 9;
const int pinMinimo = 10;
const int pinCotovelo = 11;

// Ângulos para os dedos
const int DEDO_ABERTO = 0;    // Dedo esticado
const int DEDO_FECHADO = 90;  // Dedo dobrado
const int POLEGAR_ABERTO = 0;
const int POLEGAR_FECHADO = 90;

// Posições do cotovelo
const int COTOVELO_REPOUSO = 0;
const int COTOVELO_LEVANTADO = 90;

String comando = "";

// Protótipos das funções (declaração antecipada)
void posicaoInicial();
void fazerPedra();
void fazerPapel();
void fazerTesoura();
void fazerMovimento321();
void fazerJoia();
void teste();

void setup() {
  Serial.begin(9600);
  
  // Inicializa os servos
  servoDedao.attach(pinDedao);
  servoIndicador.attach(pinIndicador);
  servoMedio.attach(pinMedio);
  servoAnelar.attach(pinAnelar);
  servoMinimo.attach(pinMinimo);
  servoCotovelo.attach(pinCotovelo);
  
  // Posição inicial: mão aberta e braço em repouso
  posicaoInicial();
  
  Serial.println("Sistema pronto! Comandos: pedra, papel, tesoura, 321, joia");
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n') {
      comando.trim(); // Remove espaços em branco
      
      if (comando == "pedra") {
        fazerPedra();
      } else if (comando == "papel") {
        fazerPapel();
      } else if (comando == "tesoura") {
        fazerTesoura();
      } else if (comando == "321") {
        fazerMovimento321();
      } else if (comando == "joia") {
        fazerJoia();
      } else {
        Serial.println("Comando não reconhecido: " + comando);
        Serial.println("Use: pedra, papel, tesoura, 321, joia");
      }
      
      comando = ""; // Limpa o comando
    } else {
      comando += c; // Constrói o comando caractere por caractere
    }
  }
  teste();
}

// Implementação das funções

void posicaoInicial() {
  // Todos os dedos abertos
  servoDedao.write(POLEGAR_ABERTO);
  servoIndicador.write(DEDO_ABERTO);
  servoMedio.write(DEDO_ABERTO);
  servoAnelar.write(DEDO_ABERTO);
  servoMinimo.write(DEDO_ABERTO);
  servoCotovelo.write(COTOVELO_REPOUSO);
  delay(500);
}

void fazerPedra() {
  Serial.println("Fazendo: PEDRA");
  
  // Fecha todos os dedos
  servoDedao.write(POLEGAR_FECHADO);
  servoIndicador.write(DEDO_FECHADO);
  servoMedio.write(DEDO_FECHADO);
  servoAnelar.write(DEDO_FECHADO);
  servoMinimo.write(DEDO_FECHADO);
  delay(1000);
}

void fazerPapel() {
  Serial.println("Fazendo: PAPEL");
  
  // Abre todos os dedos
  servoDedao.write(POLEGAR_ABERTO);
  servoIndicador.write(DEDO_ABERTO);
  servoMedio.write(DEDO_ABERTO);
  servoAnelar.write(DEDO_ABERTO);
  servoMinimo.write(DEDO_ABERTO);
  delay(1000);
}

void fazerTesoura() {
  Serial.println("Fazendo: TESOURA");
  
  // Fecha polegar, anelar e mínimo
  servoDedao.write(POLEGAR_FECHADO);
  servoAnelar.write(DEDO_FECHADO);
  servoMinimo.write(DEDO_FECHADO);
  
  // Abre indicador e médio
  servoIndicador.write(DEDO_ABERTO);
  servoMedio.write(DEDO_ABERTO);
  delay(1000);
}

void fazerMovimento321() {
  Serial.println("Fazendo: MOVIMENTO 3-2-1");
  
  // Movimento ritmado do braço durante a contagem
  for (int i = 0; i < 3; i++) {
    // Move o braço para baixo
    servoCotovelo.write(COTOVELO_REPOUSO);
    delay(400);
    
    // Move o braço para cima
    servoCotovelo.write(COTOVELO_LEVANTADO);
    delay(400);
  }
  
  // Volta para posição de repouso
  servoCotovelo.write(COTOVELO_REPOUSO);
  delay(500);
}

void fazerJoia() {
  Serial.println("Fazendo: JOIA");
  
  // Fecha todos os dedos exceto o polegar
  servoIndicador.write(DEDO_FECHADO);
  servoMedio.write(DEDO_FECHADO);
  servoAnelar.write(DEDO_FECHADO);
  servoMinimo.write(DEDO_FECHADO);
  
  // Polegar para cima (aberto)
  servoDedao.write(POLEGAR_ABERTO);
  delay(1000);
}

void teste(){
  Serial.println("Sistema pronto! Executando testes...");
  posicaoInicial();
  delay(2000);
  fazerPedra();
  delay(2000);
  posicaoInicial();
  delay(2000);
  fazerPapel();
  delay(2000);
  posicaoInicial();
  delay(2000);
  fazerTesoura();
  delay(2000);
  posicaoInicial();
  delay(2000);
  delay(2000);
  posicaoInicial();
  fazerMovimento321();
  delay(2000);
  delay(2000);
  posicaoInicial();
  fazerJoia();
  delay(2000);
}