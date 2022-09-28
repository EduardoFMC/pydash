# Alunos:
    # Eduardo Ferreira Marques Cavalcante 202006368
    # Vítor Carlos Fernandes, 190142332
    # Matheus Santos Vizu 120130050

# Disciplina:
    # Dep. Ciência da Computação - Universidade de Brasília (UnB),
    # Redes de Computadores - 2022/1

# Paper implemented
    # Adaptive Streaming of Audiovisual Content using MPEG DASH

from r2a.ir2a import IR2A
from player.parser import *
import time
from statistics import mean
from math import e

#Corrige o indice com base no valor procurado para garantir que ele prossiga na ordem
def Val_Te(throughputs, index, v): # 0 -> 1 -> 2 -> 0 -> 1 -> 2
    if((index - v) ==-1):   # se ele pedir index - 2 e o index é igual a 0, ele vai retornar o indice 1 (0 - 2 = 1)        
        return throughputs[2]     
    elif((index - v) ==-2):
        return throughputs[1]
    else:
        return throughputs[index-v]

def Calc_Te(throughputs,Ts, index, Tsi):
    
    if (throughputs[index] == 0) : #Se for a primeira vez ele copia o valor de Ts 
        throughputs[index] = Ts[Tsi]#     para ter um ponto de inicio para Te
        throughputs[2] = Ts[Tsi]
    else:
        #Calculo de p utilizando os valores mais atuais de Ts e Te
        p = (abs(Ts[Tsi] - throughputs[index]))/(throughputs[index])
        k = 21.0          # 
        Po = 0.2 # k e Po são os mesmos utilizados no artigo 
        delta = 1/(1+ e**((-k)*(p - Po)))
        #(1 − 𝛿)𝑇𝑒(𝑖 − 2)+ 𝛿𝑇𝑠(𝑖 − 1)
        throughputs[index] = (1- delta)*Val_Te(throughputs, index, 2) + delta*Ts[not Tsi] 
    
    return throughputs

def bitrate_Rc(throughputs, Ts, index, Tsi):

    # Rc(i) = (1 – µ)Te(i) 
    mi = 0.1
    Rc = (1- mi)*(Calc_Te(throughputs, Ts, index, Tsi)[index])
    return Rc

class R2AMPEG(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = [0,0,1]
        self.Ts = [0,0]
        self.Tsi = False 
        self.request_time = 0
        self.index = 0
        self.qi = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        self.Tsi = not self.Tsi

        self.Ts[self.Tsi] = (msg.get_bit_length() / t)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        avg = bitrate_Rc(self.throughputs, self.Ts, self.index, self.Tsi) #mean(self.throughputs) / 2 
        if(self.index != 2):
            self.index +=1
        else:
            self.index = 0
        self.Tsi = not self.Tsi

        selected_qi = self.qi[0]
        for i in self.qi:
            if avg *0.4 > i: #O valor de 0.4 foi obtido esperimentalmente
                selected_qi = i
            else:
                break

        msg.add_quality_id(selected_qi)
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        self.Ts[self.Tsi] = (msg.get_bit_length() / t)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass