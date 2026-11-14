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
SPLIT_INDENT = 70 # The second split hand is indented so the Play button does not cover it
HAND_SLOTS = [(10,0),(10+SPLIT_INDENT,1),(10+4*(WIDTH_IMAGE+10),0)] # (x, row) of each player hand: main hand, then the hands created by splits
MAX_HANDS = len(HAND_SLOTS) # At most 2 splits per round
RESHUFFLE_THRESHOLD = 20 # Below this many cards left, the next round starts with a new deck
BURN_CARDS = 5 # Cards burnt face down at the top of each new deck

# Card images: <value>_<suit>.gif
values = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
suits = ['diamonds','hearts','spades','clubs'] # ['♦','♥','♠','♣']


class Card(object):

    ## Card initialisation

    def __init__(self,val=None,suit=None):
        self.value,self.suit = val,suit

    ## Card value

    def getValue(self):
        return self.value

    ## Card suit

    def getSuit(self):
        return self.suit

    ## Couple

    def getCouple(self):
        return self.couple

    ## Face-up image

    def showCard(self):
        return PhotoImage(file=resource_path(self.value+'_'+self.suit+'.gif'))

    ## Face-down image

    def hideCard(self):
        return PhotoImage(file=resource_path('hidden.gif'))

    ## Ace

    def isAce(self):
        return self.value=='A'

    ## Ten-valued card

    def isPaint(self):
        return self.value =='10' or self.value =='J' or self.value =='Q' or self.value =='K'

    ## Neutral card

    def isNeutral(self):
        return self.value == '7' or self.value == '8' or self.value == '9'

    ## Small card

    def isSmall(self):
        return not(self.isPaint()) and not (self.isNeutral()) and not (self.isAce())

    ## Pair of cards

    def __eq__(self, other):
        return self.value == other.value if self and other else False


class Deck(object):

    ## Deck initialisation

    def __init__(self):
        self.cards = [Card(val,suit) for val in values for suit in suits]

    ## Deck cards

    def getCards(self):
        return self.cards

    ## Number of cards

    def getCardsCount(self):
        return len(self.cards)

    ## Shuffle sound

    def shuffleSound(self):
        PlaySound(resource_path('shuffle.wav'),SND_FILENAME)

    ## Deal sound

    def dealSound(self):
        PlaySound(resource_path('deal.wav'),SND_FILENAME)

    ## Shuffling

    def shuffle(self):
        global generator
        self.shuffleSound()
        self.cards = shuffle_cards(generator,self.cards) # rd.shuffle(self.cards)

    ## Burn cards: discard them face down, unseen and uncounted

    def burn(self,count):
        del(self.cards[:count])

    ## Draw a card

    def draw(self):
        self.dealSound()
        t = len(self.cards)
        if t>0:
            card = self.cards[0]
            del(self.cards[0])
            return card
        else:
            return None


class Dealer(object):

    ## Dealer initialisation

    def __init__(self,money):
        self.money, self.hand = money,[]

    ## Dealer's money

    def getMoney(self):
        return self.money

    def setMoney(self,money:int):
        self.money = money

    def loseMoney(self,loss:int):
        self.money -= loss

    def winMoney(self,earn:int):
        self.money+= earn

    ## Dealer's hand

    def getCards(self):
        return self.hand

    def getCardsCount(self):
        return len(self.hand)

    def resetHand(self):
        self.hand = []

    def addCard(self,card):
        self.hand.append(card)

    ## Dealer's points

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
        nb_aces = 0
        anyAce = False
        for card in self.hand:
            if card.isAce():
                nb_aces+=1
                anyAce=True
            elif card.isPaint():
                val += 10
            else :
                val+=int(card.getValue())
        # Value of the ace(s)
        while nb_aces>1:
            val += 1    # Only one ace can be worth 11 points, the others are worth 1.
            nb_aces -= 1
        if nb_aces == 1 and val + 11 <= 21:
            return val + 11
        elif anyAce:
            return val + 1
        else:
            return val


class Player(object):

    ## Player initialisation

    def __init__(self,money):
        self.money,self.bet,self.hand = money,0,[]

    ## Player's money

    def getMoney(self):
        return self.money

    def setMoney(self,money:int):
        self.money = money

    def loseMoney(self,loss:int):
        self.money -= loss

    def winMoney(self,earn:int):
        self.money+= earn

    ## Player's bet

    def getBet(self):
        return self.bet

    def setBet(self,bet:int):
        self.bet = bet

    def addBet(self,extra:int):
        self.bet += extra

    def resetBet(self):
        self.bet = 0

    ## Player's hand

    def getCards(self):
        return self.hand

    def getCardsCount(self):
        return len(self.hand)

    def addCard(self,card):
        self.hand.append(card)

    def resetHand(self):
        self.hand = []

    ## Player's points

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
        nb_aces = 0
        anyAce = False
        for card in self.hand:
            if card.isAce():
                nb_aces+=1
                anyAce=True
            elif card.isPaint():
                val += 10
            else :
                val+=int(card.getValue())
        # Value of the ace(s)
        while nb_aces>1:
            val += 1    # Only one ace can be worth 11 points, the others are worth 1.
            nb_aces -= 1
        if nb_aces == 1 and val + 11 <= 21:
            return val + 11
        elif anyAce:
            return val + 1
        else:
            return val


class Counter(object):

    ## Counter initialisation

    def __init__(self):
        self.RC = 0

    ## Running count

    def getRelativeCount(self):
        return self.RC

    ## Count update

    def addCount(self, card):
        if card.isPaint() or card.isAce():
            self.RC -= 1
        elif card.isSmall():
            self.RC += 1
        else:
            self.RC +=0


class BlackJack(object):

    ## Game initialisation

    def __init__(self,moneyDealer,moneyPlayer,minimumBet):

        self.Dealer,self.Player = Dealer(moneyDealer),Player(moneyPlayer)
        self.Deck,self.Counter = Deck(),Counter()
        self.minimumBet = minimumBet

        # Window initialisation

        self.root = Tk()
        self.root.title('BlackJack')
        self.root.iconbitmap(default=resource_path('blackjack.ico'))
        self.root.configure(background='#aa8f41')
        self.root.attributes('-fullscreen', True)

        # Canvas initialisation

        self.canvas = Canvas(self.root, width = self.root.winfo_screenwidth(), height = self.root.winfo_screenheight(),bg='white')
        self.canvas.pack(side=TOP, padx=20, pady=20)

        self.initPlayButton()
        self.initQuitButton()

        # Welcome Image

        self.showGIF('welcome.gif','WELCOME')

        # Main loop

        self.root.mainloop()

        # Application teardown

        self.root.destroy()


    def initPlayButton(self):

        playButton = Button(self.root, text ='Play', command=self.play,font = FONT_BUTTON,bg='white',fg='#aa8f41',bd=1,activeforeground='#aa8f41')
        playButton.bind('<Enter>', lambda event,button=playButton:self.on_enterButton(event,button))
        playButton.bind('<Leave>', lambda event,button=playButton:self.on_leaveButton(event,button))

        self.canvas.create_window(10, self.root.winfo_screenheight()-50, window=playButton,anchor=SW)

    def initQuitButton(self):

        exitButton = Button(self.root, text ='Quit',command=self.root.quit,font=FONT_BUTTON,bg='white',fg='#aa8f41',bd=1,activeforeground='#aa8f41')
        exitButton.bind('<Enter>', lambda event,button=exitButton:self.on_enterButton(event,button))
        exitButton.bind('<Leave>', lambda event,button=exitButton:self.on_leaveButton(event,button))

        self.canvas.create_window(self.root.winfo_screenwidth()-50, self.root.winfo_screenheight()-50, window=exitButton,anchor=SE)

    def on_enterButton(self,e,button):
        button.config(bg='OrangeRed3', fg='white')

    def on_leaveButton(self,e,button):
        button.config(bg='white',fg ='#aa8f41')

    def getCanvas(self):
        return self.canvas

    def getDealer(self):
        return self.Dealer

    def getPlayer(self):
        return self.Player

    def getDeck(self):
        return self.Deck

    def getCounter(self):
        return self.Counter

    def getMinimumBet(self):
        return self.minimumBet

    def resetDeck(self):
        self.Deck = Deck()
        self.Counter = Counter()

    def updateMoneyPlayer(self,moneyPlayer):
        self.getCanvas().itemconfigure(moneyPlayer,text='Money: %d€'% self.getPlayer().getMoney())

    def updateMoneyDealer(self,moneyDealer):
        self.getCanvas().itemconfigure(moneyDealer,text='Money: %d€'% self.getDealer().getMoney())

    def updateBetPlayer(self,betPlayer):
        self.getCanvas().itemconfigure(betPlayer,text='Bet: %d€'% self.getPlayer().getBet())

    def updateDeckCount(self,cardsRemaining):
        self.getCanvas().itemconfigure(cardsRemaining,text='Cards left: %d'% self.getDeck().getCardsCount())

    def updateScoreDealer(self,scoreDealer):
        self.getCanvas().itemconfigure(scoreDealer,text='Score: %d'% self.getDealer().getPoints())

    def updateScorePlayer(self,scorePlayer):
        self.getCanvas().itemconfigure(scorePlayer,text='Score: %d'% self.getPlayer().getPoints())

    def updateRC(self,relativeCount):
        self.getCanvas().itemconfigure(relativeCount,text='RC indicator: %d'% self.getCounter().getRelativeCount())

    def updateAfterHit(self,card,cardsRemaining,relativeCount,scorePlayer=None,scoreDealer=None):
        self.updateDeckCount(cardsRemaining)
        if scorePlayer !=None:
            self.getPlayer().addCard(card)
            self.updateScorePlayer(scorePlayer)
        if scoreDealer !=None:
            self.getDealer().addCard(card)
            self.updateScoreDealer(scoreDealer)
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

    ## Hit

    def hitChoice(self,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot=0):
        self.showGIF('hit.gif','HIT',2,True)
        self.drawPlayerCard(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot)

    ## Position of the n-th card (from 0) of the player hand shown in the given slot of HAND_SLOTS

    def cardPosition(self,slot,n,MIDDLE_VERTICAL_CANVAS):
        x, row = HAND_SLOTS[slot]
        return x+n*(WIDTH_IMAGE+10), MIDDLE_VERTICAL_CANVAS+50+row*(HEIGHT_IMAGE+10)

    ## Draw a card into the player's current hand, shown in its slot of HAND_SLOTS

    def drawPlayerCard(self,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot=0):
        PLAYER_CARD = self.getDeck().draw()

        if PLAYER_CARD!=None:
            self.updateAfterHit(PLAYER_CARD,cardsRemaining,relativeCount,scorePlayer)
            x, y = self.cardPosition(slot,self.getPlayer().getCardsCount()-1,MIDDLE_VERTICAL_CANVAS)
            self.showImage(PLAYER_CARD.showCard(),x,y,'PLAYER')
        else:
            showerror('BlackJack','No cards left in the deck')

    ## Redraw every player hand after a split moved a card to a new hand

    def redrawHands(self,hands,MIDDLE_VERTICAL_CANVAS):
        self.getCanvas().delete('PLAYER')
        for slot, hand in enumerate(hands):
            for n, card in enumerate(hand):
                x, y = self.cardPosition(slot,n,MIDDLE_VERTICAL_CANVAS)
                self.showImage(card.showCard(),x,y,'PLAYER')

    ## Stand

    def standChoice(self):
        self.showGIF('stand.gif','STAND',True,2)

    ## Double down

    def doubleChoice(self,initialBet,betPlayer,moneyPlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot=0):
        self.showGIF('double.gif','DOUBLE',True,2)
        showinfo('BlackJack',"You chose to double your bet. You will draw one last card.")
        self.getPlayer().addBet(initialBet)
        self.updateBetPlayer(betPlayer)
        self.getPlayer().loseMoney(initialBet)
        self.updateMoneyPlayer(moneyPlayer)
        self.drawPlayerCard(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot)

    ## Split pairs

    def splitChoice(self,initialBet,betPlayer,moneyPlayer):
        self.showGIF('split.gif','SPLIT',True,2)
        showinfo('BlackJack',"You chose to split your pair. Each card starts a hand with its own bet, equal to your initial bet, and you play the hands one after the other.")
        self.getPlayer().addBet(initialBet)
        self.updateBetPlayer(betPlayer)
        self.getPlayer().loseMoney(initialBet)
        self.updateMoneyPlayer(moneyPlayer)

    ## Surrender

    def surrenderChoice(self,initialBet,betPlayer,moneyPlayer,moneyDealer):
        showinfo('BlackJack',"You surrendered the round. You get back half of your initial bet and the dealer takes the other half.")
        self.getPlayer().resetBet()
        self.updateBetPlayer(betPlayer)
        self.getPlayer().winMoney(initialBet/2)
        self.updateMoneyPlayer(moneyPlayer)
        self.getDealer().winMoney(initialBet/2)
        self.updateMoneyDealer(moneyDealer)

    ## Dealer's turn

    def dealerTurn(self,cardsRemaining,TOP_VERTICAL_CANVAS,scoreDealer,relativeCount,playerPoints=None):
        if playerPoints is None:
            playerPoints = '%d points' % self.getPlayer().getPoints()
        showinfo('BlackJack',"Your turn is over. You scored %s. It is the dealer's turn." % playerPoints)
        self.getCanvas().delete('hidden')
        self.getCanvas().update()

        DEALER_CARD2 = self.getDeck().draw()
        if DEALER_CARD2!=None:
            self.updateAfterHit(DEALER_CARD2,cardsRemaining,relativeCount,None,scoreDealer)
            DEALER_IMAGE2 = DEALER_CARD2.showCard()
            self.showImage(DEALER_IMAGE2,WIDTH_IMAGE+20,TOP_VERTICAL_CANVAS)

        else:
            showerror('BlackJack','No cards left in the deck')

        while not(self.getDealer().hasR17()):
            DEALER_CARD = self.getDeck().draw()
            if DEALER_CARD!=None:
                self.updateAfterHit(DEALER_CARD,cardsRemaining,relativeCount,None,scoreDealer)
                DEALER_IMAGE = DEALER_CARD.showCard()
                self.showImage(DEALER_IMAGE,(self.getDealer().getCardsCount()-1)*(WIDTH_IMAGE+10)+10,TOP_VERTICAL_CANVAS)
            else:
                showerror('BlackJack','No cards left in the deck')

        if self.getDealer().hasBust():
            PlaySound(resource_path('bust.wav'),SND_FILENAME)
            self.showGIF('bust.gif','BUST',True,2)

        if self.getDealer().hasR21():
            PlaySound(resource_path('congrats.wav'),SND_FILENAME)
            self.showGIF('dealer21.gif','DEALER21',True,2)

        showinfo('BlackJack',"The dealer's turn is over. The dealer scored %d points."%self.getDealer().getPoints())
        time.sleep(1)

    ## Results

    def losePlayer(self):
        p = self.getPlayer()
        c = self.getDealer()
        return p.hasBust() or (c.hasR21() and p.hasVersus()) or (c.hasVersus() and p.hasVersus() and p.getPoints() < max(17,c.getPoints()))

    def winPlayer(self):
        p = self.getPlayer()
        c = self.getDealer()
        return (c.hasBust() and not(p.hasBust())) or (p.hasR21() and not(c.hasR21())) or (p.hasVersus() and c.hasVersus() and p.getPoints()>max(17,c.getPoints()))

    def tiePlayer(self):
        return not(self.winPlayer()) and not(self.losePlayer())

    ## Settle the player's current hand against the dealer (label names the hand after a split)

    def settleHand(self,stake,label='',blackjackPays=True):
        if self.tiePlayer():
            PlaySound(resource_path('bust.wav'),SND_FILENAME)
            self.showGIF('tie.gif','TIE',True,2)
            showinfo('BlackJack',label+'Tie: you get your bet back.')
            self.getPlayer().winMoney(stake)

        elif self.losePlayer():
            PlaySound(resource_path('defeat.wav'),SND_FILENAME)
            showerror('BlackJack',label+'Defeat: you lose your bet.')
            self.getDealer().winMoney(stake)

        else:
            PlaySound(resource_path('applause.wav'),SND_FILENAME)
            self.showGIF('win.gif','WIN',True,2)

            if self.getPlayer().hasBlackJackRegular() and blackjackPays:
                showinfo('BlackJack',label+'Victory: you got a BlackJack. You get your bet back and win 1.5 times your bet.')
                self.getPlayer().winMoney(stake)
                self.getPlayer().winMoney(3/2*stake)
                self.getDealer().loseMoney(3/2*stake)
            else:
                showinfo('BlackJack',label+'Victory: you get your bet back and win your bet once.')
                self.getPlayer().winMoney(stake)
                self.getPlayer().winMoney(stake)
                self.getDealer().loseMoney(stake)

    ## Bust and 21 animations for the player's current hand

    def showHandOutcome(self):
        if self.getPlayer().hasBust():
            PlaySound(resource_path('bust.wav'),SND_FILENAME)
            self.showGIF('bust.gif','BUST',True,2)

        # BlackJack with more than 2 cards
        if self.getPlayer().hasBlackJackNotRegular():
            PlaySound(resource_path('congrats.wav'),SND_FILENAME)
            self.showGIF('player21.gif','PLAYER21',True,2)

    ## Why the player's current hand cannot be split (None if it can): a pair on its first two cards, a free hand slot and enough money

    def splitRefusal(self,initialBet,handsCount=1):
        cards = self.getPlayer().getCards()
        if len(cards) != 2 or not(cards[0] == cards[1]):
            return "You can only split a pair, on your first two cards."
        if handsCount >= MAX_HANDS:
            return "You can split at most %d times per round." % (MAX_HANDS-1)
        if self.getPlayer().getMoney() < initialBet:
            return "You do not have enough money to split your pair."
        return None

    ## Basic strategy always splits aces and 8s and never splits tens: ask before splitting a pair of ten-valued cards

    def confirmSplit(self):
        if self.getPlayer().getCards()[0].isPaint():
            return askyesno('BlackJack',"Basic strategy always splits aces and 8s, and never splits tens. Split your tens anyway?",parent=self.root)
        return True

    ## Play one hand of a split (Hit, Stand, Double down or Split again) until the player stands, doubles, busts or reaches 21; return its stake, or 'split' to split it again

    def playSplitHand(self,number,handsCount,initialBet,betPlayer,moneyPlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount):
        slot = number-1
        self.updateScorePlayer(scorePlayer)
        while self.getPlayer().hasVersus():
            canSplit = self.splitRefusal(initialBet,handsCount) is None
            actions = '\n'.join(['\nHand %d' % number,'(1) Hit','(2) Stand','(3) Double down'] + (['(4) Split pairs'] if canSplit else []) + [''])
            choice = askinteger('Choose an action',actions,parent=self.root,minvalue=1,maxvalue=4 if canSplit else 3)

            if choice is None or choice == 2: # Stand
                self.standChoice()
                break

            if choice == 1: # Hit
                self.hitChoice(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot)

            if choice == 4 and self.confirmSplit(): # Split pairs again
                self.splitChoice(initialBet,betPlayer,moneyPlayer)
                return 'split'

            if choice == 3: # Double down
                if self.getPlayer().getCardsCount() > 2:
                    showinfo('BlackJack',"You can only double your bet on your first two cards.")
                    continue
                if self.getPlayer().getMoney() < initialBet:
                    showinfo('BlackJack',"You do not have enough money to double your bet.")
                    continue
                self.doubleChoice(initialBet,betPlayer,moneyPlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,slot)
                self.showHandOutcome()
                return 2*initialBet

        self.showHandOutcome()
        return initialBet

    ## Player's turn

    def play(self):

        global generator
        self.getCanvas().delete(ALL)

        minimumBet = self.getMinimumBet()
        maximumBet=self.getPlayer().getMoney()
        maxMinGap = maximumBet - minimumBet

        if (maximumBet <=0 or maxMinGap <0):
           self.showGIF('leave.gif','LEAVE',True,2)

        if(maximumBet <=0):
            showerror('Out of money', 'You have spent all your money.',parent=self.root)
            return

        if(maxMinGap < 0):
            showerror('Not enough money', 'Your money is below the required minimum bet',parent=self.root)
            return

        initialDealerMoney = self.getDealer().getMoney()

        if(initialDealerMoney < maximumBet*(3/2)):
            showinfo("Lack of money", "The casino must refill the dealer's reserves.",parent=self.root)
            return

        self.showGIF('begin.gif','BEGIN',True,2)
        self.showGIF('bet.gif','BET')

        # A new deck when too few cards are left for a round: the running count starts again and the top cards are burnt
        if self.getDeck().getCardsCount() < RESHUFFLE_THRESHOLD:
            showinfo('BlackJack',"Only %d cards left: the dealer takes a new deck." % self.getDeck().getCardsCount(),parent=self.root)
            self.resetDeck()
        newDeck = self.getDeck().getCardsCount() == len(values)*len(suits)

        self.getDeck().shuffle()
        if newDeck:
            self.getDeck().burn(BURN_CARDS)
        deckCount = self.getDeck().getCardsCount()
        self.getPlayer().resetHand()
        self.getDealer().resetHand()

        TOP_VERTICAL_CANVAS = self.root.winfo_screenheight()*0.1
        MIDDLE_VERTICAL_CANVAS = self.root.winfo_screenheight()*0.45
        END_HORIZONTAL_CANVAS = self.root.winfo_screenwidth()*0.7

        dealerLabel = self.getCanvas().create_text(10,10,text='Dealer',font=FONT_TITLE,anchor=NW)
        moneyDealer = self.getCanvas().create_text(10,40,text='Money: %d€'% initialDealerMoney,font=FONT_NORMAL,anchor=NW)
        scoreDealer = self.getCanvas().create_text(10,60,text='Score: 0',font = FONT_NORMAL,anchor=NW)
        deckLabel = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 180,10,text='Deck',font=FONT_TITLE,anchor=NW)
        cardsRemaining = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 50,50,text='Cards left: %d'% deckCount,font=FONT_NORMAL,anchor=NW)
        relativeCount = self.getCanvas().create_text(END_HORIZONTAL_CANVAS + 230,50,text='RC indicator: %d'% self.getCounter().getRelativeCount(),font=FONT_NORMAL,anchor=NW)
        self.showImage(PhotoImage(file=resource_path('deck.gif')),END_HORIZONTAL_CANVAS,80)
        playerLabel = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS-30,text='Player',font=FONT_TITLE,anchor=NW)
        moneyPlayer = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS,text='Money: %d€'% maximumBet,font=FONT_NORMAL,anchor=NW)
        scorePlayer = self.getCanvas().create_text(10,MIDDLE_VERTICAL_CANVAS+20,text='Score: 0',font=FONT_NORMAL,anchor=NW)
        betPlayer = self.getCanvas().create_text(120,MIDDLE_VERTICAL_CANVAS,text='Bet: 0€', font=FONT_NORMAL,anchor=NW)

        initialBet = askinteger(title='Initial bet',prompt='How much do you want to bet on this round?',minvalue=minimumBet,maxvalue=maximumBet)

        if initialBet is None:
            self.getCanvas().delete(ALL)
            self.initPlayButton()
            self.initQuitButton()
            self.showGIF('welcome.gif','WELCOME')
            return

        else:
            self.getCanvas().delete('BET')
            self.getCanvas().update()

            if initialBet == maximumBet:
                self.showGIF('allin.gif','ALLIN',True,2)
            self.getPlayer().setBet(initialBet)
            self.updateBetPlayer(betPlayer)
            self.getPlayer().loseMoney(initialBet)
            self.updateMoneyPlayer(moneyPlayer)

        PLAYER_CARD1 = self.getDeck().draw()

        if PLAYER_CARD1!=None:
            self.updateAfterHit(PLAYER_CARD1,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE1 = PLAYER_CARD1.showCard()
            self.showImage(PLAYER_IMAGE1,10,MIDDLE_VERTICAL_CANVAS+50,('PLAYER','PLAYER_CARD1'))

        else:
            showerror('BlackJack','No cards left in the deck')

        DEALER_CARD1 = self.getDeck().draw()
        if DEALER_CARD1!=None:
            self.updateAfterHit(DEALER_CARD1,cardsRemaining,relativeCount,None,scoreDealer)
            DEALER_IMAGE1 = DEALER_CARD1.showCard()
            self.showImage(DEALER_IMAGE1,10,TOP_VERTICAL_CANVAS,'DEALER_CARD1')

        else:
            showerror('BlackJack','No cards left in the deck')

        PLAYER_CARD2 = self.getDeck().draw()
        if PLAYER_CARD2!=None:
            self.updateAfterHit(PLAYER_CARD2,cardsRemaining,relativeCount,scorePlayer)
            PLAYER_IMAGE2 = PLAYER_CARD2.showCard()
            self.showImage(PLAYER_IMAGE2,WIDTH_IMAGE+20,MIDDLE_VERTICAL_CANVAS+50,('PLAYER','PLAYER_CARD2'))

        else:
            showerror('BlackJack','No cards left in the deck')

        self.getDeck().dealSound()
        self.showImage(Card().hideCard(),WIDTH_IMAGE+20,TOP_VERTICAL_CANVAS,'hidden')

        insuranceBet = 0 # Half the initial bet if the player takes insurance, settled once the dealer's second card is known

        if(DEALER_CARD1.isAce()):
            if self.getPlayer().getMoney() < initialBet/2:
                showinfo('BlackJack',"You do not have enough money to take insurance.")
            elif askyesno('BlackJack','Insurance?',parent=self.root):
                insuranceBet = initialBet/2
                self.getPlayer().addBet(insuranceBet)
                self.updateBetPlayer(betPlayer)
                self.getPlayer().loseMoney(insuranceBet)
                self.updateMoneyPlayer(moneyPlayer)

        time.sleep(1)

        stake = initialBet # Amount settled at the end of the round, doubled by a double down

        split = False

        if self.getPlayer().hasBlackJackRegular():
            PlaySound(resource_path('blackjack.wav'),SND_FILENAME)
            self.showGIF('player21.gif','PLAYER21',True,2)
            showinfo('Congratulations',"You got a BlackJack.")
            self.dealerTurn(cardsRemaining,TOP_VERTICAL_CANVAS,scoreDealer,relativeCount)

        else:
            while self.getPlayer().hasVersus() :

                actions = '\n'.join(['\n(1) Hit','(2) Stand','(3) Double down','(4) Split pairs','(5) Surrender\n'])

                choice = askinteger('Choose an action',actions,parent=self.root,minvalue=1,maxvalue=5)

                if choice is None or choice == 5:
                    if self.getPlayer().getCardsCount() > 2 or DEALER_CARD1.isAce():
                        showinfo('BlackJack',"You can only surrender on your first two cards, when the dealer does not show an ace.")
                        continue
                    self.surrenderChoice(initialBet,betPlayer,moneyPlayer,moneyDealer)
                    if insuranceBet: # The dealer's second card is never drawn: the insurance is lost
                        showinfo('BlackJack','Insurance: you lose your insurance.')
                        self.getDealer().winMoney(insuranceBet)
                        self.updateMoneyDealer(moneyDealer)
                    showinfo('BlackJack','Round over')
                    self.initPlayButton()
                    self.initQuitButton()
                    return

                if choice ==1: # Hit
                    self.hitChoice(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount)


                if choice ==2: # Stand
                    self.standChoice()
                    break

                if choice ==3: # Double down
                    if self.getPlayer().getCardsCount() > 2:
                        showinfo('BlackJack',"You can only double your bet on your first two cards.")
                        continue
                    if self.getPlayer().getMoney() < initialBet:
                        showinfo('BlackJack',"You do not have enough money to double your bet.")
                        continue
                    self.doubleChoice(initialBet,betPlayer,moneyPlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount)
                    stake = 2*initialBet
                    break

                if choice == 4: # Split pairs
                    refusal = self.splitRefusal(initialBet)
                    if refusal:
                        showinfo('BlackJack',refusal)
                        continue
                    if not self.confirmSplit():
                        continue
                    self.splitChoice(initialBet,betPlayer,moneyPlayer)
                    split = True
                    break

            if split:
                # The second card moves to start the second hand, then each hand gets its second card and is played in turn
                hands, stakes = [[PLAYER_CARD1],[PLAYER_CARD2]], []
                self.redrawHands(hands,MIDDLE_VERTICAL_CANVAS)

                i = 0
                while i < len(hands):
                    number = i+1
                    self.getPlayer().hand = hands[i]
                    self.drawPlayerCard(cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount,i)
                    if hands[i][0].isAce(): # Split aces get one card each, no further action and no re-split
                        showinfo('BlackJack',"Hand %d: split aces get only one card each." % number)
                        stakes.append(initialBet)
                        i += 1
                        continue
                    showinfo('BlackJack',"Hand %d: %d points." % (number,self.getPlayer().getPoints()))
                    handStake = self.playSplitHand(number,len(hands),initialBet,betPlayer,moneyPlayer,cardsRemaining,MIDDLE_VERTICAL_CANVAS,scorePlayer,relativeCount)
                    if handStake == 'split': # The second card starts a new hand right after this one, which gets a new second card
                        hands.insert(i+1,[hands[i].pop()])
                        self.redrawHands(hands,MIDDLE_VERTICAL_CANVAS)
                        continue
                    stakes.append(handStake)
                    i += 1

                points = []
                for hand in hands:
                    self.getPlayer().hand = hand
                    points.append(self.getPlayer().getPoints())
                self.getCanvas().itemconfigure(scorePlayer,text='Score: '+' / '.join('%d' % p for p in points))
                self.dealerTurn(cardsRemaining,TOP_VERTICAL_CANVAS,scoreDealer,relativeCount,', '.join('%d' % p for p in points[:-1])+' and %d points' % points[-1])

            else:
                self.showHandOutcome()
                self.dealerTurn(cardsRemaining,TOP_VERTICAL_CANVAS,scoreDealer,relativeCount)

        # Results

        self.getPlayer().resetBet()
        self.updateBetPlayer(betPlayer)

        if insuranceBet:
            if self.getDealer().hasBlackJackRegular():
                showinfo('BlackJack','Insurance: the dealer has a BlackJack. You get your insurance back and win twice your insurance.')
                self.getPlayer().winMoney(3*insuranceBet)
                self.getDealer().loseMoney(2*insuranceBet)
            else:
                showinfo('BlackJack','Insurance: the dealer has no BlackJack. You lose your insurance.')
                self.getDealer().winMoney(insuranceBet)

        if split: # A two-card 21 after a split is not a BlackJack and pays 1:1
            for number, (hand, handStake) in enumerate(zip(hands, stakes), 1):
                self.getPlayer().hand = hand
                self.settleHand(handStake,'Hand %d: ' % number,blackjackPays=False)
        else:
            self.settleHand(stake)

        self.updateMoneyPlayer(moneyPlayer)
        self.updateMoneyDealer(moneyDealer)
        showinfo('BlackJack','Round over')
        self.initPlayButton()
        self.initQuitButton()

generator = Generator()
game = BlackJack(1500,100,10)
