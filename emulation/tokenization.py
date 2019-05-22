# -*- coding: utf-8 -*-
"""Tokenization_and_generation_1_2.ipynb
Automatically generated by Colaboratory.
Original file is located at
    https://colab.research.google.com/drive/10QUynQmEIqy97uwTxL9Db9t1347NPpWs
"""

from warnings import filterwarnings

import numpy as np
import pandas as pd

filterwarnings('ignore')


#Создаем класс для кредитов с необходимыми параметрами
class Credit:
    def __init__(self, PD, LGD, value, E, D, time):
        self.PD = PD
        self.LGD = LGD
        self.P = value
        self.D = D
        self.E = E
        self.time = time
        self.defaulted = False
        self.defaultday = time

        for i in range(time):
            if np.random.uniform() > (1 - self.PD)**(1 / 365):
                self.default = True
                self.defaultday = i + 1
                break

    def print(self):
        print("\nPD=", self.PD, " LGD=", self.LGD, " value=", self.P, " E=",
              self.E, " D=", self.D, " time=", self.time, " defalt day=",
              self.defaultday)


"""c.defaulted"""


#Эта функция генерирует кредиты
def create_credits(k,
                   pd,
                   lgd,
                   value,
                   tlow=365,
                   thigh=365 * 5,
                   elow=0.1,
                   ehigh=0.2,
                   dlow=0.09,
                   dhigh=0.11):
    credits = []
    for i in range(k):
        credits.append(
            Credit(np.random.normal(pd, pd * 0.3),
                   np.random.normal(lgd, lgd * 0.2),
                   np.random.normal(value, 0.3 * value),
                   np.random.uniform(low=elow, high=ehigh),
                   np.random.uniform(low=dlow, high=dhigh),
                   np.random.randint(low=tlow, high=thigh + 1)))
    return credits


# В этом блоке мы записываем характеристики кредитов в списки, рассчитываем размер токена для
# каждого кредита и вычисляем количество токенов,на которые делим каждый кредит
def token_division(k, creditiki, D, PD, LGD, P, DI, I, R, N):
    for i in range(k):
        D.append(creditiki[i].D)
        PD.append(creditiki[i].PD)
        LGD.append(creditiki[i].LGD)
        P.append(creditiki[i].P)
    for i in range(len(D)):
        ch = (float(I) *
              (1 + float(DI))) / (1 + (float(D[i]) - float(PD[i]) *
                                       (1 + float(D[i])) * float(LGD[i])))
        R.append(ch)
        N.append(float(P[i]) / ch)


#В этой функции создаем из имеющихся списков с характеристиками кредитов датафрейм
def create_dframe(D, PD, LGD, P, DI, I, R, N):
    dframe = pd.DataFrame({
        'D': D,
        'PD': PD,
        'LGD': LGD,
        'P': P,
        'DI': DI,
        'I': I,
        'R': R,
        'N': N
    })
    credits_dframe = dframe.sort_values('N', ascending=False)
    credits_dframe = credits_dframe.reset_index()
    del credits_dframe['index']
    return credits_dframe


#Здесь непосредственно рассчитываем количество портфелей с токенами, получающихся из данных кредитов
def create_bags(credits_dframe, tok_in_bag):
    koltokbags = 0
    while len(credits_dframe["N"]) > 0:
        min_ind = 0
        #Ищем кредит из первых k с минимальным количеством токенов
        minim = credits_dframe["N"][min_ind]
        for i in range(tok_in_bag):
            if credits_dframe["N"][i] < minim:
                minim = credits_dframe["N"][i]
                min_ind = i
        #Отсекаем по минимальному кредиту определенное количество портфелей
        ob = int(credits_dframe["N"][min_ind])
        credits_dframe["N"][min_ind] = credits_dframe["N"][min_ind] - int(
            credits_dframe["N"][min_ind])
        for i in range(tok_in_bag):
            if i != min_ind:
                credits_dframe["N"][i] = credits_dframe["N"][i] - ob
        koltokbags += ob
        #ВЫкидываем кредиты с количеством токеном,равных нулю(в нашем случае меньше единицы, потому что получаются дробные количества кредитов)
        for i in range(tok_in_bag):
            if credits_dframe["N"][i] < 1:
                credits_dframe = credits_dframe.drop([i])
        credits_dframe = credits_dframe.reset_index()
        del credits_dframe['index']
        if len(credits_dframe["N"]) == 0:
            break
        min_ind = 0
        minim = credits_dframe["N"][min_ind]
        #повторяем процедуру с нахождением минимума.Если количество оставшихся кредитов меньше k, то есть невозможно составить портфель так,
        #чтобы в портфеле было максимум по одному токену с каждого кредита, то добавляем обязательства банка
        #Таким образом,мы искусственно добавляем еще несколько "кредитов"
        #чтобы их опять стало k и мы могли сделать портфели.Повторяем операцию,пока в нашем датафрейме совсем не останется кредитов.
        if len(credits_dframe["N"]) < tok_in_bag:
            for i in range(len(credits_dframe["N"])):
                if credits_dframe["N"][i] < minim:
                    minim = credits_dframe["N"][i]
                    min_ind = i
            while len(credits_dframe["N"]) < tok_in_bag:
                #добавление нашего "псевдо" кредита(векселя)
                new_record = pd.DataFrame(
                    [[
                        credits_dframe["D"][min_ind],
                        credits_dframe["PD"][min_ind],
                        credits_dframe["LGD"][min_ind],
                        credits_dframe["P"][min_ind],
                        credits_dframe["DI"][min_ind],
                        credits_dframe["I"][min_ind],
                        credits_dframe["R"][min_ind], minim
                    ]],
                    columns=['D', 'PD', 'LGD', 'P', 'DI', 'I', 'R', 'N'])
                credits_dframe = pd.concat([credits_dframe, new_record])
                credits_dframe = credits_dframe.reset_index()
                del credits_dframe['index']
    return koltokbags


def tokenize(PD, LGD, credit_value, number_of_credits):
    creditiki = create_credits(number_of_credits, PD / 100, LGD / 100,
                               credit_value)
    D = []
    PD = []
    LGD = []
    P = []
    DI = 0.05  #доходность(устанавливается банком)
    I = 1  #цена токена(устанавливается банком)
    R = []
    N = []
    token_division(number_of_credits, creditiki, D, PD, LGD, P, DI, I, R, N)
    credits_dframe = create_dframe(D, PD, LGD, P, DI, I, R, N)
    k = 2  #количество токенов в портфеле
    koltokbags = create_bags(credits_dframe, k)  #количество портфелей токенов
    return koltokbags


if __name__ == '__main__':
    tokenize(20, 10, 50, 30)
