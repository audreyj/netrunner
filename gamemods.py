import os


class Hand(object):
    def __init__(self):
        self.cards = []

    def __str__(self):  # Return a string representing the hand
        reply = ""
        if self.cards:
            for i, card in enumerate(self.cards):
                reply += "\n(" + str(i + 1) + ") " + str(card)
        else:
            reply = "<empty>"
        return reply

    def add(self, card):
        self.cards.append(card)

    def give(self, card, other_hand):
        self.cards.remove(card)
        other_hand.add(card)


class Deck(Hand):
    def shuffle(self):
        import random

        random.shuffle(self.cards)
        return "Shuffled the deck"

    def deal(self, hands, per_hand=5):
        for rounds in range(per_hand):
            for hand in hands:
                if self.cards:
                    top_card = self.cards[0]
                    self.give(top_card, hand)
                else:
                    return "Out of cards!"

    def mulligan(self, hand):
        originallen = len(hand.cards)
        while len(hand.cards):
            hand.give(hand.cards[len(hand.cards) - 1], self)
        self.shuffle()
        self.deal([hand], originallen)


class Server(object):
    def __init__(self):
        self.Icelist = Hand()
        self.installed = Hand()
        self.name = '<Empty Server>'
        self.MoreRoomForCards = True

    def __str__(self):
        return self.name

    def describeserver(self, showall=True):
        reply = "| %-15s |" % self.name
        if self.installed.cards:
            reply += "\n   => Installed Cards  => "
            for i, card in enumerate(self.installed.cards):
                if card.faceup or showall:
                    reply += "\n\t (" + str(i + 1) + ") " + str(card)
                    if card.faceup == False:
                        reply += " [===FACE DOWN===] "
                else:
                    reply += "\n\t (" + str(i + 1) + ") ===A Facedown installed card==="
                if card.currentpoints:
                    reply += " [===%d Token(s)===] " % card.currentpoints
        else:
            reply += "\n   => <No Installed Cards> "
        if self.Icelist.cards:
            reply += "\n   => Installed Ice  =>"
            for i, card in enumerate(self.Icelist.cards):
                if card.faceup or showall:
                    reply += "\n\t (" + str(i + 1) + ") " + str(card)
                    if card.faceup == False:
                        reply += " [===FACE DOWN===] "
                else:
                    reply += "\n\t (" + str(i + 1) + ") ===A Facedown installed card==="
                if card.currentpoints:
                    reply += " [===%d Token(s)===] " % card.currentpoints
        else:
            reply += "\n   => <No Ice>"
        return reply


class archives(Server):
    def __init__(self):
        Server.__init__(self)
        self.name = "Archives"
        self.MoreRoomForCards = False


class rdserver(Server):
    def __init__(self):
        Server.__init__(self)
        self.name = "R&D Server"
        self.MoreRoomForCards = False


class hqserver(Server):
    def __init__(self):
        Server.__init__(self)
        self.name = "HQ Server"
        self.MoreRoomForCards = False


class remoteserver(Server):
    def __init__(self, idnum):
        Server.__init__(self)
        self.name = "Remote Server " + str(idnum)


class Player(object):
    def __init__(self):
        self.gameboard = ''
        self.identity = ''
        self.type = ''
        self.score = 0
        self.numcredits = 5
        self.handlimit = 5
        self.numclicks = 0
        self.archivepile = Hand()
        self.ScoredCards = Hand()
        self.deck = Deck()
        self.referencedeck = Deck()
        self.hand = Hand()
        self.TurnStartActions = []
        self.TurnEndActions = []
        self.playablecardlist = []
        self.turnsummary = []

    def checkdo(self, clickcost, creditcost):
        reply = False
        if self.numclicks < clickcost:
            self.tellplayer("Not Enough Clicks for this action!")
        elif self.numcredits < creditcost:
            self.tellplayer("Not Enough Credits for this action!")
        else:
            if clickcost or creditcost:
                self.tellplayer("You paid %d click(s) and %d credit(s)." % (clickcost, creditcost))
            self.numclicks -= clickcost
            self.numcredits -= creditcost
            reply = True
        return reply

    def who_check(self, who=''):
        if who == 'opponent' and self.type == 'runner':
            return 'corp'
        elif who == 'opponent' and self.type == 'corp':
            return 'runner'
        else:
            return self.type

    def tellplayer(self, what, who=''):
        t = self.who_check(who)
        self.gameboard.TellPlayer(what, t)

    def asknum(self, question, low, high, who=''):
        t = self.who_check(who)
        return self.gameboard.GetFromPlayer(t, 'asknum', question, low, high)

    def yesno(self, question, who=''):
        t = self.who_check(who)
        return self.gameboard.GetFromPlayer(t, 'y/n', question)

    def showopts(self, opt='', who=''):
        returnlist = []
        if opt == 'status':
            for thing in self.mystatus():
                returnlist.append(thing)
            returnlist.append("| Number of Clicks = %d" % self.numclicks)
            returnlist.append("| Number of Credits = %d" % self.numcredits)
            returnlist.append("| Hand limit = %d" % self.handlimit)
            returnlist.append("| Current # of cards = %d" % len(self.hand.cards))
            returnlist.append("| Agenda Points Scored = %d" % self.score)
        elif opt in ['enemy', 'opponent']:
            self.gameboard.ShowOpponent(self.type)
        elif opt in ['hand', 'cards']:
            returnlist.append("------- Player's Hand --------")
            returnlist.append(self.hand)
        elif opt.isdigit():
            try:
                self.hand.cards[int(opt) - 1].readcard()
            except:
                returnlist.append("Invalid card number")
        elif opt == 'board':
            self.showmyboard()
        elif opt == 'archives':
            returnlist.append(self.archivepile)
        elif opt in ['all', 'deck']:
            for i, card in enumerate(self.referencedeck.cards):
                self.tellplayer("(" + str(i + 1) + ") " + str(card))
            choice = self.asknum("Choose card: ", 1, len(self.referencedeck.cards) + 1)
            self.referencedeck.cards[choice - 1].readcard()
        else:
            returnlist.append("Valid SHOW objects: HAND, STATUS, DECK, ARCHIVES, BOARD")
        for thing in returnlist:
            self.tellplayer(thing, who)

    def drawcard(self, clickcost=1):
        if clickcost not in range(0, 4): clickcost = 1
        self.tellplayer('Draw 1 card')
        if self.checkdo(clickcost, 0):
            self.deck.deal([self.hand], 1)
            self.turnsummary.append('Drew a card')

    def takecredit(self, clickcost=1):
        self.tellplayer('Gain 1 credit from bank')
        if clickcost not in range(0, 4): clickcost = 1
        if self.checkdo(clickcost, 0):
            self.numcredits += 1
            self.turnsummary.append('Took a credit from the bank')
            self.tellplayer("Number of Credits: " + str(self.numcredits))

    def playcard(self, cardnum=0, clickcost=1):
        if cardnum == 0:
            self.tellplayer("Cards on the board that you can play: ")
            for i, card in enumerate(self.playablecardlist):
                self.tellplayer("(" + str(i + 1) + ") " + str(card))
            choice = self.asknum("Choose card to Play: ", 1, len(self.playablecardlist) + 1)
            if choice == 'cancel': return 0
            chosencard = self.playablecardlist[choice - 1]
        elif int(cardnum) in range(1, len(self.hand.cards) + 1):
            chosencard = self.hand.cards[int(cardnum) - 1]
            if chosencard.type not in ['Operation', 'Event']:
                self.tellplayer("Did you mean to INSTALL this card?  It can't be PLAYED")
                return 0
        else:
            self.tellplayer("Not the right card?")
            return False
        if 'cardaction' in dir(chosencard):
            self.tellplayer("Play " + chosencard.name)
            self.turnsummary.append('Played ' + str(chosencard))
            chosencard.cardaction()
            if chosencard.subtype == 'Transaction' and self.identity == 'WC':
                self.tellplayer("WC Power: Gain 1 credit")
                self.takecredit(0)

    def installcard(self, cardnum=0):  # install something
        try:
            chosencard = self.hand.cards[int(cardnum) - 1]
        except:
            self.tellplayer("Non-valid card choice")
            return 0
        if chosencard.type in ['Operation', 'Event']:
            self.tellplayer("Did you mean to PLAY this card?")
        else:
            self.tellplayer("Installing " + str(chosencard))
            chosencard.InstallAction()

    def trashmine(self, opt=''):
        chosencard = self.choosefromboard(True)
        if chosencard:
            question = "Really trash " + str(chosencard.name) + "?? "
            if self.gameboard.GetFromPlayer('y/n', question):
                if not chosencard.installedin:
                    chosencard.faceup = False
                chosencard.trashaction(chosencard.faceup)
                self.turnsummary.append('Trashed a card')

    def TurnStart(self):
        self.firstcall = True
        self.turnsummary = []
        # print self.TurnStartActions
        for dothing in self.TurnStartActions:
            dothing(0)

    def TurnEnd(self):
        while len(self.hand.cards) > self.handlimit:
            self.tellplayer("You have too many cards in your hand.")
            self.showopts('hand')
            ans = self.asknum("Discard which card? ", 1, len(self.hand.cards) + 1)
            self.hand.cards[ans - 1].trashaction()
        for dothing in self.TurnEndActions:
            dothing()
        os.system('cls')
        self.tellplayer("-------- Opponent Turn Summary ---------", 'opponent')
        for thing in self.turnsummary:
            self.tellplayer("  - " + thing, 'opponent')

    def playturn(self):
        self.tellplayer("---------- It Is Your Turn (%s) -------------" % self.type)
        self.numclicks = self.totalclicks
        self.TurnStart()
        if self.type == 'corp': self.drawcard(0)
        while 1:
            self.tellplayer("-----------------------------------------------")
            self.tellplayer("It is %s turn.  You have %d clicks remaining." % (self.type, self.numclicks))
            if not self.numclicks:
                self.tellplayer("(Type 'end' to end your turn)")
            userinput = self.gameboard.GetFromPlayer(self.type, '> ')
            wordlist = userinput.split()
            if not self.numclicks and wordlist[0] == 'end':
                break
            elif wordlist[0] in self.actions:
                do = self.actions[wordlist[0]]
                # try:
                do(*wordlist[1:])
            # except:
            #	self.tellplayer("Not understanding your nouns")
            else:
                self.tellplayer("action not in list: ")
                self.tellplayer(self.actions.keys())
        self.TurnEnd()


class CorpPlayer(Player):
    def __init__(self):
        Player.__init__(self)
        self.type = 'corp'
        self.totalclicks = 3
        self.serverlist = [hqserver(), rdserver(), archives()]
        self.actions = {"show": self.showopts, "advance": self.advancecard,
                        "install": self.installcard, "draw": self.drawcard,
                        "take": self.takecredit, "purge": self.purgevirus,
                        "trash": self.trashsomething, "play": self.playcard,
                        "rez": self.rezcard}

    def showmyboard(self, who=''):
        for server in self.serverlist:
            self.tellplayer(server.describeserver(), who)

    def choosefromboard(self, showhand=False):
        self.showopts("board")
        cardlist = []
        for server in self.serverlist:
            for ice in server.Icelist.cards:
                cardlist.append(ice)
            for card in server.installed.cards:
                cardlist.append(card)
        if showhand:
            for card in self.hand.cards:
                cardlist.append(card)
        for i, card in enumerate(cardlist):
            if card.installedin:
                location = self.serverlist[card.installedin - 1].name
            else:
                location = "your hand"
            self.tellplayer("(" + str(i + 1) + ") " + str(card) + " --> in " + location)
        choice = self.asknum("Choose card: ", 1, len(cardlist) + 1)
        if choice == 'cancel':
            return 0
        chosencard = cardlist[choice - 1]
        return chosencard

    def mystatus(self):
        returnstring = ["--------- Corporation Player ----------"]
        returnstring.append("| Identity = Haas-Biodroid")
        returnstring.append("| ID Power = The first time you install a card each turn, gain 1 credit")
        returnstring.append("| Remaining Cards in HQ = %d" % len(self.deck.cards))
        returnstring.append("| Number of Cards in Archives = %d" % len(self.archivepile.cards))
        return returnstring

    def advancecard(self, clickcost=1, amt=1):  # advance a card
        chosencard = self.choosefromboard()
        if not chosencard:
            return 0
        elif not chosencard.advancetotal:
            self.tellplayer("Not an advanceable card")
            return 0
        if self.checkdo(clickcost, 1):
            chosencard.currentpoints += amt
            self.turnsummary.append('Advanced a card')
            self.tellplayer("Advanced %s" % chosencard.name)
            if chosencard.advancetotal <= chosencard.currentpoints:
                chosencard.ScoreAction()

    def purgevirus(self, opt=''):  # purge virus counters
        self.tellplayer('purge virus counters')
        self.turnsummary.append('purged virus counters')
        # clickcost = 3
        # creditcost = 0
        if self.checkdo(3, 0):
            self.tellplayer("Purge.... not implemented ^_^")

    def trashsomething(self, opt=''):  # trash a card from somewhere
        if not opt:
            self.tellplayer("One of your cards, or one of your opponent's?")
            self.tellplayer("\t (1) One of mine \n\t (2) One of the runner's")
            opt = self.asknum("> ", 1, 3)
        if opt == 1:
            self.trashmine()
        elif opt == 2:
            self.tellplayer('Trash 1 resource if runner is tagged')
            if self.gameboard.rplayer.numtags:
                chosencard = 1
                while chosencard:
                    chosencard = self.gameboard.rplayer.choosefromboard(False, 'opponent')
                    if chosencard and chosencard.type == 'Resource':
                        if self.checkdo(1, 2):
                            chosencard.trashaction()
                            self.turnsummary.append('Trashed %s' % chosencard)
                            chosencard = 0
                    else:
                        self.tellplayer("Not a resource card?")
            else:
                self.tellplayer("Runner is not tagged!")
        elif opt == 3:
            self.tellplayer("Trash one of the runner's programs")
            chosencard = 1
            while chosencard:
                chosencard = self.gameboard.rplayer.choosefromboard(False, 'opponent')
                if chosencard and chosencard.type == "Program":
                    self.tellplayer("Trashing " + str(chosencard))
                    chosencard.trashaction()
                    chosencard = 0
                else:
                    self.tellplayer("Not a Program card?")
        else:
            self.tellplayer("You didn't make a valid choice, I'm cancelling out.")

    def rezcard(self, opt=''):  # rez a card that's on the board already
        chosencard = self.choosefromboard()
        if not chosencard:
            return 0
        elif chosencard.faceup or chosencard.rezcost == '<None>':
            self.tellplayer("This card does not need rezzing")
            return 0
        elif self.checkdo(0, chosencard.rezcost):
            chosencard.faceup = True
            chosencard.RezAction()
            self.turnsummary.append('Rezzed ' + str(chosencard))
            self.tellplayer("Rezzed %s" % chosencard.name)

    def RunActions(self, servernum, icecounter):
        actions = {"show": self.showopts, "play": self.playcard,
                   "rez": self.rezcard}
        chosenserver = self.serverlist[servernum - 1]
        while 1:
            self.tellplayer("---------------------------")
            self.tellplayer("Runner is making a run on: " + str(chosenserver))
            self.tellplayer("Approaching Ice #" + str(icecounter + 1))
            self.tellplayer("Take an action? (Type 'end' when done)")
            userinput = self.gameboard.GetFromPlayer('corp', '> ')
            wordlist = userinput.split()
            if wordlist[0] == 'end':
                return 0
            elif wordlist[0] in actions:
                do = actions[wordlist[0]]
                do(*wordlist[1:])
            else:
                self.tellplayer("action not in list: ")
                self.tellplayer(actions.keys())


class RunnerPlayer(Player):
    def __init__(self):
        Player.__init__(self)
        self.type = 'runner'

    def mystatus(self):  # separate out identities and powers
        returnstring = ["---------------- Runner Player ---------------"]
        returnstring.append("| Identity: Kate McCaffrey (Natural)")
        returnstring.append("| ID Power: First install cost on hardware or program -1")
        returnstring.append("| Program Memory Limit: %d" % self.programlimit)
        returnstring.append("| Current Memory Usage: %d" % self.memoryused)
        returnstring.append("| Current Number of Tags: %d" % self.numtags)
        returnstring.append("| Current Link Strength: %d" % self.numlinks)
        return returnstring

        self.programlimit = 4
        self.memoryused = 0
        self.boardhand = Hand()
        self.numtags = 0
        self.numlinks = 1
        self.usedcardslist = []
        self.preventset = {}
        self.totalclicks = 4
        self.actions = {"show": self.showopts, "run": self.standardrun,
                        "install": self.installcard, "draw": self.drawcard,
                        "take": self.takecredit, "remove": self.removetags,
                        "trash": self.trashmine, "play": self.playcard}
    def showmyboard(self, who=''):
        self.tellplayer("-------------- Runner's Rig -------------", who)
        for card in self.boardhand.cards:
            if card.currentpoints:
                self.tellplayer("\n\t-> %s  [=== %d Token(s) ===]" % (str(card), card.currentpoints), who)
            else:
                self.tellplayer("\n\t->" + str(card), who)

    def choosefromboard(self, showhand=False, who=''):
        cardlist = []
        i = 0
        for card in self.boardhand.cards:
            cardlist.append(card)
            self.tellplayer("(" + str(i + 1) + ") " + str(card), who)
            i += 1
        if showhand:
            for card in self.hand.cards:
                cardlist.append(card)
                self.tellplayer("(" + str(i + 1) + ") " + str(card) + " (in your hand)", who)
                i += 1
        choice = self.asknum("Choose card: ", 1, len(cardlist) + 1, who)
        if choice == 'cancel': return 0
        chosencard = cardlist[choice - 1]
        return chosencard

    def removetags(self, opt=''):
        if self.numtags and self.checkdo(1, 2):
            self.numtags -= 1
            self.tellplayer("Removed one tag")
            self.turnsummary.append('Removed a tag')

    def PreventCheck(self, var):  # check with player to prevent damage
        reply = False
        cardlist = [x for x in self.preventset.keys() if self.preventset[x] == var]
        while cardlist:
            for i, card in enumerate(cardlist):
                self.tellplayer("\t (0) - Do nothing")
                self.tellplayer("\t (" + str(i + 1) + ") - Play " + str(card))
            ans = self.asknum("> ", 0, len(cardlist) + 1)
            if not ans:
                break
            elif cardlist[ans - 1].cardaction():
                reply = True
                break
        return reply

    def breaksubroutines(self, ice):
        self.usedcardslist = []
        while 1:
            self.tellplayer("You've encountered ice - time to get to breaking")
            ice.printsubroutines()
            self.tellplayer("Use commands 'show', 'play', or 'spend'")
            self.tellplayer("(Type 'end' when done)")
            choosebreak = False
            userinput = self.gameboard.GetFromPlayer('runner', '> ')
            wordlist = userinput.split()
            if wordlist[0] == 'end':
                return 0
            elif wordlist[0] == 'show':
                if wordlist[1] == 'ice':
                    ice.readcard()
                else:
                    self.showopts(*wordlist[1:])
            elif ice.spendclickoption and wordlist[0] == 'spend':
                if self.checkdo(1, 0):
                    choosebreak = True
            elif wordlist[0] == 'play':
                chosencard = self.choosefromboard()
                if 'breakaction' in dir(chosencard) and chosencard.breakaction(ice):
                    self.usedcardslist.append(chosencard)
                    choosebreak = True
            else:
                self.tellplayer("Invalid option for breaking, try again")
            if choosebreak:
                ice.printsubroutines()
                s = self.asknum("Break which subroutine: ", 1, len(ice.subroutines) + 1)
                ice.subroutines[s][1] = False

    def exposecard(self):  # not finished
        self.gameboard.ShowOpponent('runner')

    def standardrun(self, clickcost=1):
        if self.checkdo(clickcost, 0):
            self.gameboard.ShowOpponent('runner')
            self.tellplayer('---------------------------')
            for i, server in enumerate(self.gameboard.cplayer.serverlist):
                self.tellplayer("\t (" + str(i + 1) + ") " + str(server))
            servernum = self.asknum("Choose server to run on: ", 1, i + 2)
            if servernum == 'cancel': return False
            self.turnsummary.append('Made a run')
            if self.gameboard.StartRun(servernum):
                self.gameboard.AccessCards(servernum)
            else:
                self.tellplayer("Run Failed!")
            for card in self.usedcardslist:
                card.Reset()
	

