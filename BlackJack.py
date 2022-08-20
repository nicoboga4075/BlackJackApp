import math,time,os,random as rd,matplotlib.pyplot as plt
from itertools import *
from winsound import *
from tkinter import *
from tkinter.messagebox import *
from tkinter.simpledialog import *

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def Generator(SEED=123456789,a=8*191119970+5,c=1,m=2**48):
    xi = SEED
    while True:
        xf = (a * xi + c) % m
        xi=xf
        yield xf

def get_py_iid(Generator):
    return str(sorted([v for v in range(1,10001)] ,key = lambda i:next(Generator))[0])

def shuffle_cards(Generator,cards):
    return sorted(cards,key = lambda i:next(Generator))

FONT_TITLE, FONT_NORMAL , FONT_BUTTON = ('Tahoma',16),('Tahoma',10),('Tahoma',10,'bold')
WIDTH_IMAGE,HEIGHT_IMAGE = 130,180
WIDTH_GIF, HEIGHT_GIF = 384,270
RATIO_GIF_WIDTH,RATIO_GIF_HEIGHT = 0.35,0.32

values = ['2','3','4','5','6','7','8','9','10','V','D','R','A']
colors = ['carreau','coeur','pique','trefle'] # ['\u2666','\u2665','\u2660','\u2663']


class Card(object):

    ## Initialisation de la carte

    def __init__(self,val=None,col=None):
        self.value,self.color = val,col

    ## Valeur de la carte

    def getValue(self):
        return self.value

    ## Couleur de la carte

    def getColor(self):
        return self.color

    ## Couple

    def getCouple(self):
        return self.couple

    ## Image face visible

    def showCard(self):
        return PhotoImage(file=resource_path(self.value+'_'+self.color+'.gif'))

    ## Image face cachée

    def hideCard(self):
        return PhotoImage(file=resource_path('hidden.gif'))

    ## As

    def isAs(self):
        return self.value=='A'

    ## Bûche

    def isPaint(self):
        return self.value =='10' or self.value =='V' or self.value =='D' or self.value =='R'

    ## Carte neutre

    def isNeutral(self):
        return self.value == '7' or self.value == '8' or self.value == '9'

    ## Carte faible

    def isSmall(self):
        return not(self.isPaint()) and not (self.isNeutral()) and not (self.isAs())

    ## Paire de cartes

    def __eq__(self, other):
        return self.value == other.value if self and other else False


class Deck(object):

    ## Initialisation du paquet

    def __init__(self):
        self.cards = [Card(val,col) for val in values for col in colors]

    ## Cartes du paquet

    def getCards(self):
        return self.cards

    ## Nombre de cartes

    def getCardsCount(self):
        return len(self.cards)

    ## Melange du paquet

    def melanger(self):
        PlaySound(resource_path('melange.wav'),SND_FILENAME)

    ## Distribution d'une carte

    def distribuer(self):
        PlaySound(resource_path('tirage.wav'),SND_FILENAME)

    ## Battage

    def battre(self):
        global generator
        self.melanger()
        self.cards = shuffle_cards(generator,self.cards) # rd.shuffle(self.cards)

    ## Tirer une carte

    def tirer(self):
        self.distribuer()
        t = len(self.cards)
        if t>0:
            card = self.cards[0]
            del(self.cards[0])
            return card
        else:
            return None


class Croupier(object):

    ## Initialisation du croupier

    def __init__(self,money):
        self.money, self.main = money,[]

    ## Argent du croupier

    def getMoney(self):
        return self.money

    def setMoney(self,money:int):
        self.money = money

    def loseMoney(self,loss:int):
        self.money -= loss

    def winMoney(self,earn:int):
        self.money+= earn

    ## Main du croupier

    def getCards(self):
        return self.main

    def getCardsCount(self):
        return len(self.main)

    def reinitMain(self):
        self.main = []

    def addCard(self,card):
        self.main.append(card)

    ## Points du croupier

    def hasBlackJackRegular(self):
        return self.hasR21() and self.getCardsCount() == 2

    def hasBlackJackNotRegular(self):
        return self.hasR21() and self.getCardsCount() >= 3

    def hasR21(self):
        return self.getPoints()== 21

    def hasBust(self):
        return self.getPoints() > 21

    def hasVersus(self):
        return not(self.hasR21()) and not(self.hasBust())

    def hasR17(self):
        return self.getPoints() >= 17

    def getPoints(self):
        val = 0
        nb_as = 0
        anyAs = False
        for card in self.main:
            if card.isAs():
                nb_as+=1
                anyAs=True
            elif card.isPaint():
                val += 10
            else :
                val+=int(card.getValue())
        # Valeur de l'as ou des as
        while nb_as>1:
            val += 1    # Un seul as peut valoir 11 pts, les autres valent 1.
            nb_as -= 1
        if nb_as == 1 and val + 11 <= 21:
            return val + 11
        elif anyAs:
            return val + 1
        else:
            return val


class Player(object):

    ## Initialisation du joueur

    def __init__(self,money):
        self.money,self.mise,self.main = money,0,[]

    ## Argent du joueur

    def getMoney(self):
        return self.money

    def setMoney(self,money:int):
        self.money = money

    def loseMoney(self,loss:int):
        self.money -= loss

    def winMoney(self,earn:int):
        self.money+= earn

    ## Mise du joueur

    def getMise(self):
        return self.mise

    def setMise(self,mise:int):
        self.mise = mise

    def addMise(self,supp:int):
        self.mise += supp

    def reinitMise(self):
        self.mise = 0

    ## Main du joueur

    def getCards(self):
        return self.main

    def getCardsCount(self):
        return len(self.main)

    def addCard(self,card):
        self.main.append(card)

    def reinitMain(self):
        self.main = []

    ## Points du joueur

    def hasBlackJackRegular(self):
        return self.hasR21() and self.getCardsCount() == 2

    def hasBlackJackNotRegular(self):
        return self.hasR21() and self.getCardsCount() >= 3

    def hasR21(self):
        return self.getPoints()== 21

    def hasBust(self):
        return self.getPoints() > 21

    def hasVersus(self):
        return not(self.hasR21()) and not(self.hasBust())

    def getPoints(self):
        val = 0
        nb_as = 0
        anyAs = False
        for card in self.main:
            if card.isAs():
                nb_as+=1
                anyAs=True
            elif card.isPaint():
                val += 10
            else :
                val+=int(card.getValue())
        # Valeur de l'as ou des as
        while nb_as>1:
            val += 1    # Un seul as peut valoir 11 pts,les autres valent 1.
            nb_as -= 1
        if nb_as == 1 and val + 11 <= 21:
            return val + 11
        elif anyAs:
            return val + 1
        else:
            return val


class Counter(object):

    ## Initialisation du compteur

    def __init__(self):
        self.RC = 0

    ## Compte relatif

    def getRelativeCount(self):
        return self.RC

    ## Actualisation du compte

    def addCount(self, card):
        if card.isPaint() or card.isAs():
            self.RC -= 1
        elif card.isSmall():
            self.RC += 1
        else:
            self.RC +=0


class BlackJack(object):

    ## Initialisation du jeu

    def __init__(self,moneyCroupier,moneyPlayer,miseMinimale):

        self.Croupier,self.Player = Croupier(moneyCroupier),Player(moneyPlayer)
        self.Deck,self.Counter = Deck(),Counter()
        self.miseMinimale = miseMinimale

        # Initialisation de la fenêtre

        self.root = Tk()
        self.root.title('BlackJack')
        self.root.iconbitmap(default=resource_path('blackjack.ico'))
        self.root.configure(background='#aa8f41')
        self.root.attributes('-fullscreen', True)

        # Initialisation du canvas

        self.canvas = Canvas(self.root, width = self.root.winfo_screenwidth(), height = self.root.winfo_screenheight(),bg='white')
        self.canvas.pack(side=TOP, padx=20, pady=20)

        self.initPlayButton()
        self.initQuitButton()

        # Welcome Image

        self.showGIF('welcome.gif','WELCOME')

        # Boucle principale

        self.root.mainloop()

        # Destruction de l'application

        self.root.destroy()


    def initPlayButton(self):

        playButton = Button(self.root, text ='Jouer', command=self.play,font = FONT_BUTTON,bg='white',fg='#aa8f41',bd=1,activeforeground='#aa8f41')
        playButton.bind('<Enter>', lambda event,button=playButton:self.on_enterButton(event,button))
        playButton.bind('<Leave>', lambda event,button=playButton:self.on_leaveButton(event,button))

        self.canvas.create_window(10, self.root.winfo_screenheight()-50, window=playButton,anchor=SW)

    def initQuitButton(self):

        exitButton = Button(self.root, text ='Quitter',command=self.root.quit,font=FONT_BUTTON,bg='white',fg='#aa8f41',bd=1,activeforeground='#aa8f41')
        exitButton.bind('<Enter>', lambda event,button=exitButton:self.on_enterButton(event,button))
        exitButton.bind('<Leave>', lambda event,button=exitButton:self.on_leaveButton(event,button))

        self.canvas.create_window(self.root.winfo_screenwidth()-50, self.root.winfo_screenheight()-50, window=exitButton,anchor=SE)

    def on_enterButton(self,e,button):
        button.config(bg='OrangeRed3', fg='white')

    def on_leaveButton(self,e,button):
        button.config(bg='white',fg ='#aa8f41')

    def getCanvas(self):
        return self.canvas

    def getCroupier(self):
        return self.Croupier

    def getPlayer(self):
        return self.Player

    def getDeck(self):
        return self.Deck

    def getCounter(self):
        return self.Counter

    def getMiseMinimale(self):
        return self.miseMinimale

    def reinitDeck(self):
        self.Deck = Deck()

    def updateMoneyPlayer(self,moneyPlayer):
        self.getCanvas().itemconfigure(moneyPlayer,text='Argent : %d€'% self.getPlayer().getMoney())

    def updateMoneyCroupier(self,moneyCroupier):
        self.getCanvas().itemconfigure(moneyCroupier,text='Argent : %d€'% self.getCroupier().getMoney())

    def updateMisePlayer(self,misePlayer):
        self.getCanvas().itemconfigure(misePlayer,text='Mise : %d€'% self.getPlayer().getMise())

    def updateDeckCount(self,cardsRemaining):
        self.getCanvas().itemconfigure(cardsRemaining,text='Cartes restantes : %d'% self.getDeck().getCardsCount())

    def updateScoreCroupier(self,scoreCroupier):
        self.getCanvas().itemconfigure(scoreCroupier,text='Score : %d'% self.getCroupier().getPoints())

    def updateScorePlayer(self,scorePlayer):
        self.getCanvas().itemconfigure(scorePlayer,text='Score : %d'% self.getPlayer().getPoints())

    def updateRC(self,relativeCount):
        self.getCanvas().itemconfigure(relativeCount,text='Indicateur RC : %d'% self.getCounter().getRelativeCount())

    def updateAfterHit(self,card,cardsRemaining,relativeCount,scorePlayer=None,scoreCroupier=None):
        self.updateDeckCount(cardsRemaining)
        if scorePlayer !=None:
            self.getPlayer().addCard(card)
            self.updateScorePlayer(scorePlayer)
        if scoreCroupier !=None:
            self.getCroupier().addCard(card)
            self.updateScoreCroupier(scoreCroupier)
        self.getCounter().addCount(card)
        self.updateRC(relativeCount)

    def showImage(self,image,x,y,tag=None):
        self.getCanvas().create_image(x, y, image = image, anchor = NW,tag=tag)
        setattr(self.getCanvas(), 'image'+get_py_iid(generator), image)
        self.getCanvas().update()

    def showGIF(self,image,tag,autoDestruction=False,seconds=1):
        self.showImage(PhotoImage(file=resource_path(image)),self.root.winfo_screenwidth()*RATIO_GIF_WIDTH,self.root.winfo_screenheight()*RATIO_GIF_HEIGHT,tag=tag)
        if autoDestruction:
            time.sleep(seconds)
            self.getCanvas().delete(tag)
            self.getCanvas().update()

    ## Tirer une carte

    def hitChoice(self,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount):
        self.showGIF('hit.gif','HIT',2,True)
        PLAYER_CARTE = self.getDeck().tirer()

        if PLAYER_CARTE!=None:
            self.updateAfterHit(PLAYER_CARTE,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE, n = PLAYER_CARTE.showCard(),self.getPlayer().getCardsCount()
            self.showImage(PLAYER_IMAGE,(n-1)*(WIDTH_IMAGE+10)+10,MIDDLE_VERTICAL_CANVAS+50)
        else:
            pass

    ## Rester

    def standChoice(self):
        self.showGIF('stand.gif','STAND',True,2)

    ## Doubler la mise

    def doubleChoice(self,miseInitiale,misePlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount):
        self.showGIF('double.gif','DOUBLE',True,2)
        showinfo('BlackJack',"Vous avez choisi de doubler votre mise. Vous allez tirer une dernière carte.")
        self.getPlayer().addMise(miseInitiale)
        self.updateMisePlayer(misePlayer)
        PLAYER_CARTE = self.getDeck().tirer()

        if PLAYER_CARTE!=None:
            self.updateAfterHit(PLAYER_CARTE,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE, n = PLAYER_CARTE.showCard(),self.getPlayer().getCardsCount()
            self.showImage(PLAYER_IMAGE,(n-1)*(WIDTH_IMAGE+10)+10,MIDDLE_VERTICAL_CANVAS+50)

        else:
            pass

    ## Séparer les paires

    def splitChoice(self,miseInitiale,misePlayer,moneyPlayer,moneyCroupier,cardsRemaining):
        self.showGIF('split.gif','SPLIT',True,2)
        showinfo('BlackJack',"Vous avez choisi de séparer vos paires. Vous piochez une dernière carte. Votre mise est donc doublée.")

    ## Abandonner

    def surrenderChoice(self,miseInitiale,misePlayer,moneyPlayer,moneyCroupier):
        showinfo('BlackJack',"Vous avez abandonné la partie. Vous récupérez la moitié de votre mise de départ et le croupier récupère l'autre moitié.")
        self.getPlayer().reinitMise()
        self.updateMisePlayer(misePlayer)
        self.getPlayer().winMoney(miseInitiale/2)
        self.updateMoneyPlayer(moneyPlayer)
        self.getCroupier().winMoney(miseInitiale/2)
        self.updateMoneyCroupier(moneyCroupier)

    ## Tour du croupier

    def tourCroupier(self,cardsRemaining,TOP_VERTICAL_CANVAS,scoreCroupier,relativeCount):
        showinfo('BlackJack',"Votre tour est terminé. Vous avez obtenu %d points. C'est au tour du croupier."%self.getPlayer().getPoints())
        self.getCanvas().delete('hidden')
        self.getCanvas().update()

        CROUPIER_CARTE2 = self.getDeck().tirer()
        if CROUPIER_CARTE2!=None:
            self.updateAfterHit(CROUPIER_CARTE2,cardsRemaining,relativeCount,None,scoreCroupier)
            CROUPIER_IMAGE2 = CROUPIER_CARTE2.showCard()
            self.showImage(CROUPIER_IMAGE2,WIDTH_IMAGE+20,TOP_VERTICAL_CANVAS)

        else:
            showerror('BlackJack','Aucun carte restante dans le deck')

        while not(self.getCroupier().hasR17()):
            CROUPIER_CARTE = self.getDeck().tirer()
            if CROUPIER_CARTE!=None:
                self.updateAfterHit(CROUPIER_CARTE,cardsRemaining,relativeCount,None,scoreCroupier)
                CROUPIER_IMAGE = CROUPIER_CARTE.showCard()
                self.showImage(CROUPIER_IMAGE,(self.getCroupier().getCardsCount()-1)*(WIDTH_IMAGE+10)+10,TOP_VERTICAL_CANVAS)
            else:
                showerror('BlackJack','Aucun carte restante dans le deck')

        if self.getCroupier().hasBust():
            PlaySound(resource_path('bust.wav'),SND_FILENAME)
            self.showGIF('bust.gif','BUST',True,2)

        if self.getCroupier().hasR21():
            PlaySound(resource_path('congrats.wav'),SND_FILENAME)
            self.showGIF('dealer21.gif','DEALER21',True,2)

        showinfo('BlackJack','Le tour du croupier est terminé. Il a obtenu %d points.'%self.getCroupier().getPoints())
        time.sleep(1)

    ## Résultats

    def losePlayer(self):
        p = self.getPlayer()
        c = self.getCroupier()
        return p.hasBust() or (c.hasR21() and p.hasVersus()) or (c.hasVersus() and p.hasVersus() and p.getPoints() < max(17,c.getPoints()))

    def winPlayer(self):
        p = self.getPlayer()
        c = self.getCroupier()
        return (c.hasBust() and not(p.hasBust())) or (p.hasR21() and not(c.hasR21())) or (p.hasVersus() and c.hasVersus() and p.getPoints()>max(17,c.getPoints()))

    def equalityPlayer(self):
        return not(self.winPlayer()) and not(self.losePlayer())

    ## Tour du joueur

    def play(self):

        global generator
        self.getCanvas().delete(ALL)

        miseMinimale = self.getMiseMinimale()
        miseMaximale=self.getPlayer().getMoney()
        ecartMaxMin = miseMaximale - miseMinimale

        if (miseMaximale <=0 or ecartMaxMin <0):
           self.showGIF('leave.gif','LEAVE',True,2)

        if(miseMaximale <=0):
            showerror('Argent épuisé', 'Vous avez dépensé tout votre argent.',parent=self.root)
            return

        if(ecartMaxMin < 0):
            showerror('Argent insuffisant', 'Votre argent est inférieur à la mise minimale requise',parent=self.root)
            return

        moneyInitialCroupier = self.getCroupier().getMoney()

        if(moneyInitialCroupier < miseMaximale*(3/2)):
            showinfo("Manque d'argent", 'Le casino doit remplir les réserves du croupier.',parent=self.root)
            return

        self.showGIF('begin.gif','BEGIN',True,2)
        self.showGIF('bet.gif','BET')

        deckCount = self.getDeck().getCardsCount()

         # TODO : si deckCount > 0

        self.getDeck().battre()
        self.getPlayer().reinitMain()
        self.getCroupier().reinitMain()

        TOP_VERTICAL_CANVAS = self.root.winfo_screenheight()*0.1
        MIDDLE_VERTICAL_CANVAS = self.root.winfo_screenheight()*0.45
        END_HORIZONTAL_CANVAS = self.root.winfo_screenwidth()*0.7

        croupierLabel = self.getCanvas().create_text(10,10,text='Croupier',font=FONT_TITLE,anchor=NW)
        moneyCroupier = self.getCanvas().create_text(10,40,text='Argent : %d€'% moneyInitialCroupier,font=FONT_NORMAL,anchor=NW)
        scoreCroupier = self.getCanvas().create_text(10,60,text='Score : 0',font = FONT_NORMAL,anchor=NW)
        deckLabel = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 180,10,text='Deck',font=FONT_TITLE,anchor=NW)
        cardsRemaining = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 50,50,text='Cartes restantes : %d'% deckCount,font=FONT_NORMAL,anchor=NW)
        relativeCount = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 230,50,text='Indicateur RC : %d'% self.getCounter().getRelativeCount(),font=FONT_NORMAL,anchor=NW)
        self.showImage(PhotoImage(file=resource_path('deck.gif')),END_HORIZONTAL_CANVAS,80)
        playerLabel = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS-30,text='Joueur',font=FONT_TITLE,anchor=NW)
        moneyPlayer = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS,text='Argent : %d€'% miseMaximale,font=FONT_NORMAL,anchor=NW)
        scorePlayer = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS+20,text='Score : 0',font=FONT_NORMAL,anchor=NW)
        misePlayer = self.getCanvas().create_text(80,MIDDLE_VERTICAL_CANVAS+20,text='Mise : 0€', font=FONT_NORMAL,anchor=NW)

        miseInitiale = askinteger(title='Mise initale',prompt='Combien voulez-vous miser pour cette partie ?',minvalue=miseMinimale,maxvalue=miseMaximale)

        if miseInitiale is None:
            self.getCanvas().delete(ALL)
            self.initPlayButton()
            self.initQuitButton()
            self.showGIF('welcome.gif','WELCOME')
            return

        else:
            self.getCanvas().delete('BET')
            self.getCanvas().update()

            if miseInitiale == miseMaximale:
                self.showGIF('allin.gif','ALLIN',True,2)
            self.getPlayer().setMise(miseInitiale)
            self.updateMisePlayer(misePlayer)
            self.getPlayer().loseMoney(miseInitiale)
            self.updateMoneyPlayer(moneyPlayer)

        PLAYER_CARTE1 = self.getDeck().tirer()

        if PLAYER_CARTE1!=None:
            self.updateAfterHit(PLAYER_CARTE1,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE1 = PLAYER_CARTE1.showCard()
            self.showImage(PLAYER_IMAGE1,10,MIDDLE_VERTICAL_CANVAS+50,'PLAYER_CARTE1')

        else:
            showerror('BlackJack','Aucun carte restante dans le deck')

        CROUPIER_CARTE1 = self.getDeck().tirer()
        if CROUPIER_CARTE1!=None:
            self.updateAfterHit(CROUPIER_CARTE1,cardsRemaining,relativeCount,None,scoreCroupier)
            CROUPIER_IMAGE1 = CROUPIER_CARTE1.showCard()
            self.showImage(CROUPIER_IMAGE1,10,TOP_VERTICAL_CANVAS,'CROUPIER_CARTE1')

        else:
            showerror('BlackJack','Aucun carte restante dans le deck')

        PLAYER_CARTE2 = self.getDeck().tirer()
        if PLAYER_CARTE2!=None:
            self.updateAfterHit(PLAYER_CARTE2,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE2 = PLAYER_CARTE2.showCard()
            self.showImage(PLAYER_IMAGE2,WIDTH_IMAGE+20,MIDDLE_VERTICAL_CANVAS+50,'PLAYER_CARTE2')

        else:
            showerror('BlackJack','Aucun carte restante dans le deck')

        self.getDeck().distribuer()
        self.showImage(Card().hideCard(),WIDTH_IMAGE+20,TOP_VERTICAL_CANVAS,'hidden')

        # TODO : si Croupier a blackjack, insurance = True => si (joueur a blackjack) self.getPlayer().winself.getPlayer().winMoney(2*miseAssurance) and self.getCroupier().winMoney(miseAssurance) ** insurance = False => self.getPlayer().loseMoney(miseAssurance)

        # TODO : si insurance

        if(CROUPIER_CARTE1.isAs()):
            insurance = askyesno('BlackJack','Assurance ?',parent=self.root)
            miseAssurance = miseInitiale/2
            if insurance:
                self.getPlayer().addMise(miseInitiale/2)
                self.updateMisePlayer(misePlayer)
            else:
                pass

        else:
            pass

        time.sleep(1)

        if self.getPlayer().hasBlackJackRegular():
            PlaySound(resource_path('blackjack.wav'),SND_FILENAME)
            self.showGIF('player21.gif','PLAYER21',True,2)
            showinfo('Félicitations',"Vous avez obtenu un BlackJack.")
            self.tourCroupier(cardsRemaining,TOP_VERTICAL_CANVAS,scoreCroupier,relativeCount)

        else:
# TODO : empecher de cliquer sur split si pas de paire et sur doubler si pas possible -> manque d'argent + doubler mise si assurance ?
            hasPairs = PLAYER_CARTE1 == PLAYER_CARTE2

            split = False

            while self.getPlayer().hasVersus() :

                actions = '\n'.join(['\n(1) Tirer une carte','(2) Rester','(3) Doubler la mise','(4) Séparer les paires','(5) Abandonner\n'])

                choice = askinteger('Choisissez une action',actions,parent=self.root,minvalue=1,maxvalue=5)

                if choice is None or choice == 5:
                    self.surrenderChoice(miseInitiale,misePlayer,moneyPlayer,moneyCroupier)
                    showinfo('BlackJack','Partie terminée')
                    self.initPlayButton()
                    self.initQuitButton()
                    return

                if choice ==1: # Tirer une carte
                    self.hitChoice(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount)


                if choice ==2: # Rester
                    self.standChoice()
                    break

                if choice ==3: # Doubler la mise
                    self.doubleChoice(miseInitiale,misePlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount)
                    break

                if choice == 4 and hasPairs: # Séparer les paires
                    self.splitChoice(miseInitiale,misePlayer,moneyPlayer,moneyCroupier,cardsRemaining)
                    split = True
                    break


            if split:
                main1, main2 = [self.getPlayer().main[0]],[self.getPlayer().main[1]]
                mise1, mise2 = miseInitiale,miseInitiale
                self.getCanvas().delete('PLAYER_CARTE2')
                self.getCanvas().update()
                self.showImage(PLAYER_IMAGE2,10,MIDDLE_VERTICAL_CANVAS+240)

                # showinfo('BlackJack','Carte n°1')
                # self.getPlayer().setMain(main1)
                # score1 = self.getPlayer().getPoints()
                #
                # while self.getPlayer().hasVersus() :
                #     listeActions = ['\n(1) Tirer une carte','(2) Rester','(3) Doubler la mise','(4) Abandonner\n']
                #     actions = '\n'.join(listeActions)
                #
                # showinfo('BlackJack','Carte n°2')
                # self.getPlayer().setMain(main2)
                # score2 = self.getPlayer().getPoints()
                #
                # while self.getPlayer().hasVersus() :
                #     listeActions = ['\n(1) Tirer une carte','(2) Rester','(3) Doubler la mise','(4) Abandonner\n']
                #     actions = '\n'.join(listeActions)



            # Bust or not Bust ?

            if self.getPlayer().hasBust():
                PlaySound(resource_path('bust.wav'),SND_FILENAME)
                self.showGIF('bust.gif','BUST',True,2)

            # BlackJack avec plus de 2 cartes

            if self.getPlayer().hasBlackJackNotRegular():
                PlaySound(resource_path('congrats.wav'),SND_FILENAME)
                self.showGIF('player21.gif','PLAYER21',True,2)

            self.tourCroupier(cardsRemaining,TOP_VERTICAL_CANVAS,scoreCroupier,relativeCount)

        # Résultats

        self.getPlayer().reinitMise()
        self.updateMisePlayer(misePlayer)

        if self.equalityPlayer():
            PlaySound(resource_path('bust.wav'),SND_FILENAME)
            self.showGIF('equality.gif','EQUALITY',True,2)
            showinfo('BlackJack','Egalité : Vous récupérez votre mise.')
            self.getPlayer().winMoney(miseInitiale)

        elif self.losePlayer():
            PlaySound(resource_path('defaite.wav'),SND_FILENAME)
            showerror('BlackJack','Défaite : Vous perdez votre mise.')
            self.getCroupier().winMoney(miseInitiale)

        else:
            PlaySound(resource_path('applaudissement.wav'),SND_FILENAME)
            self.showGIF('win.gif','WIN',True,2)


            if self.getPlayer().hasBlackJackRegular() and not(split):
                showinfo('BlackJack','Victoire : Vous avez obtenu un BlackJack. Vous récupérez votre mise et vous gagnez 1,5 fois votre mise.')
                self.getPlayer().winMoney(miseInitiale)
                self.getPlayer().winMoney(3/2*miseInitiale)
                self.getCroupier().loseMoney(3/2*miseInitiale)
            else:
                showinfo('BlackJack','Victoire : Vous récupérez votre mise et vous gagnez une fois votre mise.')
                self.getPlayer().winMoney(miseInitiale)
                self.getPlayer().winMoney(miseInitiale)
                self.getCroupier().loseMoney(miseInitiale)

        self.updateMoneyPlayer(moneyPlayer)
        self.updateMoneyCroupier(moneyCroupier)
        showinfo('BlackJack','Partie terminée')
        self.initPlayButton()
        self.initQuitButton()

generator = Generator()
game = BlackJack(1500,100,10)

        # TODO sous réserve que le croupier n'ait pas d'as et avant tout tirage supplémentaire
        # TODO qu'une carte par as si paire d'as
        # TODO 2 split maximum par main
        # TODO 5/6 cartes brulees d'amblée
        #TODO Ne pas split lorsque paire de dix uniquement paire de 8 et d'as
