import os
import sys
import gamemods
import cards


class gameboard(object):
    def __init__(self):
        self.cplayer = gamemods.CorpPlayer()
        self.cplayer.gameboard = self
        self.rplayer = gamemods.RunnerPlayer()
        self.rplayer.gameboard = self
        self.continuerun = True

    def LoadDeck(self, player, deckname):
        possibles = {'HB': cards.HBdeck, 'WC': cards.WCdeck, 'NBN': cards.NBNdeck,
                     'Jinteki': cards.Jdeck, 'Natural': cards.naturaldeck,
                     'Cyborg': cards.cyborgdeck, 'Noise': cards.noisedeck,
                     'runnerdeck': cards.defaultrunnerdeck, 'corpdeck': cards.defaultcorpdeck}
        self.TellPlayer("Populated the deck with:", player.type)
        newlist = []
        for key in possibles.keys():
            if key.lower() in deckname.lower():  # if the key is in the input, use that deck
                for card in possibles[key]:
                    player.deck.add(card())
                self.TellPlayer(key + ': ' + str(len(possibles[key])), player.type)
                newlist.extend(list(set(possibles[key])))
                if 'runner' not in key and 'corp' not in key:
                    player.identity = key
        for i, card in enumerate(player.deck.cards):
            card.player = player
            card.id = i
        for card in newlist:  # reference deck for read-only
            player.referencedeck.add(card())
        for card in player.referencedeck.cards:
            card.player = player
        player.deck.shuffle()
        player.deck.deal([player.hand], player.handlimit)
        self.TellPlayer(player.hand, player.type)
        if self.GetFromPlayer(player.type, 'y/n', "Mulligan? > "):
            player.deck.mulligan(player.hand)

    def ShowOpponent(self, callertype):
        if callertype == 'runner':
            self.cplayer.showopts("status", 'opponent')
            for server in self.cplayer.serverlist:
                self.TellPlayer(server.describeserver(False), 'runner')
        else:
            self.rplayer.showopts("status", 'opponent')
            self.rplayer.showmyboard('opponent')

    def StartRun(self, servernum, bypass=False):
        chosenserver = self.cplayer.serverlist[servernum - 1]
        icecounter = len(chosenserver.Icelist.cards)
        self.winrun = True
        while self.winrun and icecounter:
            self.TellPlayer("Approaching outermost Ice card...", 'runner')
            icecounter -= 1
            icecard = chosenserver.Icelist.cards[icecounter]
            os.system('cls')
            self.cplayer.RunActions(servernum, icecounter)
            if icecard.faceup and not bypass:
                icecard.readcard()
                icecard.EncounterAction()
                self.rplayer.breaksubroutines(icecard)
                icecard.cardaction()
                icecard.ResetIce()
            if icecounter and self.GetFromPlayer('runner', 'y/n', "Jack out? > "):
                self.winrun = False
                icecounter = 0
        return self.winrun

    def AccessCall(self, chosencard, location, skiptrash=True):
        self.TellPlayer(chosencard, 'runner')
        if chosencard.type == 'Agenda':
            self.TellPlayer(
                "You've stolen %s! You gained %d agenda points." % (chosencard.name, chosencard.agendapoints), 'runner')
            self.rplayer.score += chosencard.agendapoints
            if self.rplayer.score >= 7:
                self.TellPlayer("Runner player reaches 7 agenda points and wins", 'bothplayers')
                sys.exit(0)
            location.give(chosencard, self.rplayer.ScoredCards)
            if chosencard.installedin:
                self.cplayer.serverlist[chosencard.installedin - 1].MoreRoomForCards = True
            chosencard.advancetotal = 0
            chosencard.type = "Agenda: Scored"
            chosencard.player = self.rplayer
            self.rplayer.turnsummary.append('Scored ' + str(chosencard))
            return True
        if skiptrash and 'RunnerAccessed' in dir(chosencard):
            chosencard.RunnerAccessed()
        if skiptrash and chosencard.trashcost != '<None>':
            self.TellPlayer("Pay %d Credits to trash %s?" % (chosencard.trashcost, chosencard.name), 'runner')
            if self.GetFromPlayer('runner', 'y/n', "> ") and self.rplayer.checkdo(0, chosencard.trashcost):
                chosencard.trashaction(True, location)
        else:
            self.TellPlayer("Nothing to be done with this card, returning it...", 'runner')

    def AccessCards(self, servernum, numcards=1):
        chosenserver = self.cplayer.serverlist[servernum - 1]
        self.TellPlayer("Run Successful, Accessed " + str(chosenserver), 'runner')
        self.TellPlayer("Accessing Installed Cards...", 'runner')
        cardlist = chosenserver.installed.cards
        numaccessible = len(cardlist)
        while numaccessible:
            reply = ''
            for i, card in enumerate(cardlist):
                reply += "\n\t (" + str(i + 1) + ") "
                if card.faceup:
                    reply += str(card)
                else:
                    reply += "==== A FACEDOWN CARD ===="
                if card.currentpoints:
                    reply += " [==== %d token(s)====]" % card.currentpoints
            self.TellPlayer(reply, 'runner')
            num = self.GetFromPlayer('runner', 'asknum', "Choose card: ", 1, len(cardlist) + 1)
            self.AccessCall(cardlist[num - 1], chosenserver.installed)
            numaccessible -= 1
        self.TellPlayer("No installed cards to access", 'runner')
        if servernum == 1:  # HQ server
            handlen = len(self.cplayer.hand.cards)
            self.TellPlayer("Pick a card from 1 to " + str(handlen), 'runner')
            ans = self.GetFromPlayer('runner', 'asknum', "> ", 1, handlen + 1)
            self.AccessCall(self.cplayer.hand.cards[ans - 1], self.cplayer.hand)
        elif servernum == 2:  # R&D server
            for i in range(numcards):
                self.TellPlayer("Accessing a card from R&D...", 'runner')
                self.AccessCall(self.cplayer.deck.cards[i], self.cplayer.deck)
        elif servernum == 3:  # Archives
            self.TellPlayer("Accessing Archives...", 'runner')
            for card in self.cplayer.archivepile.cards:
                self.AccessCall(card, self.cplayer.archivepile, False)

    def StartTrace(self, basetrace):
        self.TellPlayer("Corporation initiates trace", 'bothplayers')
        self.TellPlayer("Add credits to enhance trace? (%d base)" % basetrace, 'corp')
        self.TellPlayer("Your current credits: " + str(self.cplayer.numcredits), 'corp')
        addt = self.GetFromPlayer('corp', 'asknum', "Credits to add: ", 0, self.cplayer.numcredits + 1)
        if addt == 'cancel':
            return False
        else:
            atk = basetrace + addt
            self.TellPlayer("Corporation trace strength: %d" % atk, 'bothplayers')
            links = self.rplayer.numlinks
            self.TellPlayer("Runner Link strength: %d" % links, 'bothplayers')
            if links >= atk:
                self.TellPlayer("Runner avoids trace", 'bothplayers')
                return False
            else:
                self.TellPlayer("Your current credits: " + str(self.rplayer.numcredits), 'runner')
                question = "Pay %d credits to avoid trace? " % (atk - links)
                if self.GetFromPlayer('runner', 'y/n', question) and self.rplayer.checkdo(0, atk - links):
                    self.TellPlayer("Runner pays to avoid trace", 'bothplayers')
                    return False
                else:
                    self.rplayer.numtags += 1
                    self.TellPlayer("Runner receives 1 tag", 'bothplayers')
                    return True

    def DoDamage(self, amt, type):
        if type == 'brain':
            self.TellPlayer("Runner player takes %d brain damage" % amt, 'bothplayers')
            if self.rplayer.handlimit < amt:
                self.TellPlayer("RUNNER SUSTAINS FATAL DAMAGE ==> RUNNER LOSES", 'bothplayers')
                sys.exit(0)
            self.rplayer.handlimit -= amt
        else:
            if type == 'net' and self.rplayer.PreventCheck('netdamage'): amt -= 1
            self.TellPlayer("Runner player takes %d net/meat damage" % amt, 'bothplayers')
            if len(self.rplayer.hand.cards) < amt:
                self.TellPlayer("RUNNER SUSTAINS FATAL DAMAGE ==> RUNNER LOSES", 'bothplayers')
                sys.exit(0)
            for dmg in range(amt):
                self.rplayer.showopts('hand')
                ans = self.GetFromPlayer('runner', 'asknum', "Discard which card? ", 1,
                                         len(self.rplayer.hand.cards) + 1)
                self.rplayer.hand.cards[ans - 1].trashaction()

    def ExposeCard(self):
        pass

    def TellPlayer(self, what, whichplayer='activeplayer'):
        print(whichplayer + ": ", what, "/ (" + whichplayer + ")")

    def GetFromPlayer(self, player, prompt, question='', low=0, high=1):
        response = None
        if prompt == 'y/n':
            while response not in ("y", "n", "yes", "no"):
                response = input(question).lower()
            if response in ('y', 'yes'):
                response = True
            elif response in ('n', 'no'):
                response = False
        elif prompt == 'asknum':
            a = list(range(low, high))
            a.append('cancel')
            while response not in a:
                response = input(question)
                try:
                    response = int(response)
                except:
                    pass
        else:
            response = input(prompt).lower()
        return response

    def playgame(self):
        os.system('cls')
        self.LoadDeck(self.cplayer, 'corpdeckHB')
        os.system('cls')
        self.LoadDeck(self.rplayer, 'runnerdecknatural')
        os.system('cls')
        while self.cplayer.score < 7 and self.rplayer.score < 7:
            self.cplayer.playturn()
            self.rplayer.playturn()


newgame = gameboard()
newgame.playgame()