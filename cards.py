import sys
import gamemods


class Card(object):
    def __init__(self):
        self.name = '<None>'
        self.rezcost = '<None>'
        self.supertype = '<None>'
        self.type = '<None>'
        self.subtype = '<No Subtype>'
        self.icestr = '<None>'
        self.cardtext = '<None>'
        self.faceup = True
        self.currentpoints = 0
        self.takeaction = []
        self.installedin = 0
        self.player = ''
        self.id = '<None>'

    def __str__(self):
        reply = self.name + " (" + self.type + ": " + self.subtype + ")"
        return reply

    def tellplayer(self, what):
        # whichplayer = self.player.type
        self.player.gameboard.TellPlayer(what)

    def readcard(self):
        self.tellplayer("----- Card Name = %s -------" % self.name)
        self.tellplayer("| Card Type = %s:%s" % (self.type, self.subtype))
        if self.type == 'Program':
            self.tellplayer("| Memory Unit Cost = " + str(self.programcost))
        if self.type in ['Ice', 'Program']:
            self.tellplayer("| Ice Strength = " + str(self.icestr))
        elif self.type == 'Agenda':
            self.tellplayer("| Advancement Points needed = " + str(self.advancetotal))
            self.tellplayer("| Agenda Points = " + str(self.agendapoints))
        elif self.type == 'Operation':
            pass
        elif hasattr(self, 'trashcost'):
            self.tellplayer("| Trash Cost = " + str(self.trashcost))
        if self.supertype == 'Runnercard':
            self.tellplayer("| Install Cost = " + str(self.rezcost))
        elif self.supertype == 'Corpcard':
            self.tellplayer("| Rez Cost = " + str(self.rezcost))
        self.tellplayer("| Card Text = " + self.cardtext)
        self.tellplayer("| Card ID# = " + str(self.id))
        self.tellplayer("------------------------------\n")


# ====================================================
#  BEGIN SUPERTYPE CLASS DEFINITIONS
#====================================================

class corpcard(Card):
    def __init__(self):
        Card.__init__(self)
        self.trashcost = '<None>'
        self.supertype = "Corpcard"
        self.advancetotal = 0

    def InstallAction(self, clickcost=1):
        reply = False
        self.player.showopts("board")
        printout = ''
        for i, server in enumerate(self.player.serverlist):
            printout += "\n\t (" + str(i + 1) + ") " + str(server)
        printout += "\n\t (" + str(i + 2) + ") New Remote Server"
        self.tellplayer(printout)
        maxnum = len(self.player.serverlist) + 1
        madechoice = 0
        while not madechoice:
            x = self.player.asknum("Choose Server to Install Card in: ",
                                   1, maxnum + 1)
            if x == 'cancel':
                break
            elif x == maxnum:
                self.player.serverlist.append(gamemods.remoteserver(x - 3))
                self.tellplayer("creating new remote server %s" % self.player.serverlist[maxnum - 1].name)
            chosenserver = self.player.serverlist[x - 1]
            if self.type in ['Asset', 'Agenda']:
                if chosenserver.MoreRoomForCards:
                    if self.player.checkdo(clickcost, 0):
                        self.player.hand.give(self, chosenserver.installed)
                        self.tellplayer("Putting card in %s" % chosenserver.name)
                        chosenserver.MoreRoomForCards = False
                        madechoice = x
                else:
                    self.tellplayer("No cards can be installed in this server")
            elif self.type == 'Upgrade':
                if self.player.checkdo(clickcost, 0):
                    self.player.hand.give(self, chosenserver.installed)
                    self.tellplayer("Putting card in %s" % chosenserver.name)
                    madechoice = x
            elif self.type == 'Ice':
                creditcost = 0
                for icecard in chosenserver.Icelist.cards:
                    creditcost += 1
                if self.player.checkdo(clickcost, creditcost):
                    self.player.hand.give(self, chosenserver.Icelist)
                    madechoice = x
                    self.tellplayer("Installed Ice %s on server: %s" % (self.name, chosenserver.name))
        if madechoice:
            self.faceup = False
            self.installedin = madechoice
            self.player.turnsummary.append('Installed a card in ' + str(chosenserver.name))
            if self.player.identity == 'HB' and self.player.firstcall:
                self.player.firstcall = False
                self.tellplayer("HB Power: Gain 1 credit")
                self.player.takecredit(0)
            reply = True
        return reply

    def trashaction(self, faceup=False, location=''):
        self.faceup = faceup
        self.currentpoints = 0
        if self in self.player.playablecardlist:
            self.player.playablecardlist.remove(self)
        if location:
            cardlocation = location
        elif self.installedin:
            if self.type == 'Ice':
                cardlocation = self.player.serverlist[self.installedin - 1].Icelist
            else:
                cardlocation = self.player.serverlist[self.installedin - 1].installed
        else:
            cardlocation = self.player.hand
        if self.installedin and self.type != 'Ice':
            self.player.serverlist[self.installedin - 1].MoreRoomForCards = True
        if self.faceup:
            for thing in self.takeaction:
                if thing in self.player.TurnStartActions:
                    self.player.TurnStartActions.remove(thing)
        self.installedin = 0
        cardlocation.give(self, self.player.archivepile)
        if faceup:
            carddesc = self.name
        else:
            carddesc = "a card facedown"
        self.player.turnsummary.append('Trashed ' + carddesc)
        self.tellplayer("Trashed " + str(self))


class runnercard(Card):
    def __init__(self):
        Card.__init__(self)
        self.supertype = "Runnercard"
        self.programcost = 0

    def InstallAction(self, clickcost=1):
        reply = False
        discount = 0
        if self.player.firstcall and self.type in ['Program', 'Hardware']:
            self.tellplayer("Natural Power: -1 cost of install")
            discount = 1
        if self.player.memoryused + self.programcost > self.player.programlimit:
            self.tellplayer("Memory Limit Exceeded, cannot install this card!")
            return reply
        if self.player.checkdo(clickcost, max(self.rezcost - discount, 0)):
            self.currentpoints = 0
            self.player.hand.give(self, self.player.boardhand)
            self.player.memoryused += self.programcost
            self.installedin = 1
            self.RezAction()
            self.player.turnsummary.append('Installed ' + str(self))
            if discount: self.player.firstcall = False
            reply = True
        return reply

    def RezAction(self):
        pass

    def reup(self, azero):
        pass

    def trashaction(self, check=True):
        if self in self.player.hand.cards:
            self.player.hand.give(self, self.player.archivepile)
        elif self in self.player.boardhand.cards:
            if check and self.player.PreventCheck('trash'): return False
            self.player.boardhand.give(self, self.player.archivepile)
            self.player.memoryused -= self.programcost
            for thing in self.takeaction:
                if thing in self.player.TurnStartActions:
                    self.player.TurnStartActions.remove(thing)
        self.currentpoints = 0
        self.installedin = 0
        if self in self.player.playablecardlist:
            self.player.playablecardlist.remove(self)
        self.player.turnsummary.append('Trashed ' + str(self))
        self.tellplayer("Trashed " + str(self))


#=================================================
#  BEGIN C-CARD TYPE CLASS DEFINITIONS
#=================================================

class IceCard(corpcard):
    def __init__(self):
        corpcard.__init__(self)
        self.type = 'Ice'
        self.subroutines = {}  #{number: [name, unbroken]}
        self.spendclickoption = False

    def printsubroutines(self):
        reply = ''
        if self.subroutines:
            for id in self.subroutines.keys():
                reply += "\n\t Subroutine" + str(id) + ": " + self.subroutines[id][0]
                if self.subroutines[id][1]:
                    reply += "   [=== UNBROKEN ===]"
                else:
                    reply += "   [=== BROKEN ===]"
        else:
            reply = '<No Subroutines>'
        self.tellplayer(reply + '\n')

    def RezAction(self):
        self.faceup = True

    def EncounterAction(self):
        pass

    def EndRun(self, opt='', opt2=''):
        self.player.gameboard.winrun = False

    def InitTrace(self, opt=0, extra=''):
        if self.player.gameboard.StartTrace(int(opt)):
            self.ExtraAction()

    def LoseClick(self, opt=0, opt2=''):
        for i in range(int(opt)):
            clicks = self.player.gameboard.rplayer.numclicks
            num = int(opt)
            self.player.gameboard.rplayer.numclicks = max(clicks - num, 0)

    def TrashProg(self, opt=0, opt2=''):
        for i in range(int(opt)):
            self.player.trashsomething(3)

    def damage(self, opt=0, opt2='', opt3=''):
        self.player.gameboard.DoDamage(int(opt), opt2)

    def ExtraAction(self):
        pass

    def cardaction(self):
        self.printsubroutines()
        actions = {"end": self.EndRun, "trace": self.InitTrace,
                   "lose": self.LoseClick, "trash": self.TrashProg,
                   "do": self.damage}
        for id in self.subroutines.keys():
            if self.subroutines[id][1]:
                wordlist = self.subroutines[id][0].lower().split()
                actions[wordlist[0]](*wordlist[1:])

    def ResetIce(self):
        for id in self.subroutines.keys():
            self.subroutines[id][1] = True


class AgendaCard(corpcard):
    def __init__(self):
        corpcard.__init__(self)
        self.type = 'Agenda'
        self.agendapoints = '<None>'

    def RezAction(self):
        self.tellplayer("Don't Rez this card, fool!")

    def ScoreAction(self):
        self.tellplayer("You scored %s!  You gained %d agenda points." % (self.name, self.agendapoints))
        self.player.score += self.agendapoints
        if self.player.score >= 7:
            self.tellplayer("Corp player reaches 7 agenda points and wins")
            sys.exit(0)
        location = self.player.serverlist[self.installedin - 1]
        location.installed.give(self, self.player.ScoredCards)
        location.MoreRoomForCards = True
        self.installedin = 0
        self.advancetotal = 0
        self.type = 'Agenda: Scored'
        self.player.turnsummary.append('Scored an Agenda')


class UpgradeCard(corpcard):
    def __init__(self):
        corpcard.__init__(self)
        self.type = "Upgrade"


class AssetCard(corpcard):
    def __init__(self):
        corpcard.__init__(self)
        self.type = 'Asset'

    def RezAction(self):
        self.tellplayer("No Rez Action associated with this card")


class OperationCard(corpcard):
    def __init__(self):
        corpcard.__init__(self)
        self.type = 'Operation'

    def InstallAction(self):
        reply = False
        clickcost = 1
        if self.player.checkdo(clickcost, self.rezcost):
            self.tellplayer("You played %s" % self.name)
            self.trashaction(True)
            reply = True
        return reply


#==================================================
#  BEGIN R-CARD TYPE CLASS DEFINITIONS
#==================================================

class EventCard(runnercard):
    def __init__(self):
        runnercard.__init__(self)
        self.type = "Event"


class ProgramCard(runnercard):
    def __init__(self):
        runnercard.__init__(self)
        self.type = "Program"

    def IBtypecheck(self, type, ice):
        if type not in ice.subtype:
            self.tellplayer("Ice not %s type" % type)
            return False
        else:
            return True

    def IBincreasestr(self, ice, factor=1):
        if ice.icestr > self.icestr:
            question = "Pay %d credits to increase strength to equal ice? > " % (ice.icestr - self.icestr) * factor
            if self.player.yesno(question) and self.player.checkdo(0, (ice.icestr - self.icestr) * factor):
                self.icestr = ice.icestr

    def Reset(self):
        pass


class ResourceCard(runnercard):
    def __init__(self):
        runnercard.__init__(self)
        self.type = "Resource"


class HardwareCard(runnercard):
    def __init__(self):
        runnercard.__init__(self)
        self.type = "Hardware"


#==================================================
#  BEGIN INDIVIDUAL C-CARD DEFINITIONS
#==================================================

#Default Corp Deck Cards
class PadCampaign(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = 'Pad Campaign'
        self.subtype = 'Advertisement'
        self.rezcost = 2
        self.cardtext = 'Gain 1 credit when your turn begins'
        self.trashcost = 4

    def RezAction(self):
        self.takeaction = [self.reup, self.player.takecredit]
        for thing in self.takeaction:
            self.player.TurnStartActions.append(thing)

    def reup(self, *args):
        self.tellplayer("THE POWER OF PAD CAMPAIGN GIVES YOU:")


class MiningCorp(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = 'Melange Mining Corp.'
        self.rezcost = 1
        self.cardtext = 'Pay 3 clicks: Gain 7 credits'
        self.trashcost = 4

    def RezAction(self):
        self.type = 'Operation'
        self.player.playablecardlist.append(self)

    def cardaction(self):
        if self.player.checkdo(3, 0):
            self.tellplayer("Gained 7 credits")
            self.player.numcredits += 7


class Hunter(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = 'Hunter'
        self.rezcost = 1
        self.cardtext = 'Subroutine1: Trace3'
        self.icestr = 4
        self.subtype = 'Tracer'
        self.subroutines = {1: ['Trace 3', True]}


class Enigma(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Enigma"
        self.subtype = 'Code Gate'
        self.rezcost = 3
        self.icestr = 2
        self.cardtext = 'Subroutine1: Runner loses 1 click.  Subroutine2: End the run'
        self.subroutines = {1: ['Lose 1 click', True], 2: ['End the run', True]}


class WallofStatic(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Wall of Static"
        self.subtype = "Barrier"
        self.rezcost = 3
        self.icestr = 3
        self.cardtext = "Subroutine1: End the run"
        self.subroutines = {1: ['End the run', True]}


class PriorityRequisition(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Priority Requisition"
        self.agendapoints = 3
        self.advancetotal = 5
        self.cardtext = "When you score Priority Requisition, you may rez a piece of ice ignoring all costs"

    def ScoreAction(self):
        AgendaCard.ScoreAction(self)
        self.tellplayer("You may now rez a piece of ice at no cost")
        escapeclause = 1
        while escapeclause:
            chosencard = self.player.choosefromboard()
            if chosencard:
                if chosencard.type == 'Ice' and not chosencard.faceup:
                    chosencard.faceup = True
                    self.tellplayer("Rezzed %s" % chosencard.name)
                    escapeclause = 0
                else:
                    self.tellplayer("Not the card you wanted?")
            else:
                escapeclause = 0


class PSF(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Private Security Force"
        self.agendapoints = 2
        self.advancetotal = 4
        self.cardtext = "If the Runner is tagged, Private Security Force gains: 'Pay 1 Click: Do 1 meat damage'"

    def ScoreAction(self):
        AgendaCard.ScoreAction(self)
        self.tellplayer("Private Security Force gains the power: 'Pay 1 Click: Do 1 meat damage'.")
        self.type = 'Operation'  #change type to operation so it can be played
        self.player.playablecardlist.append(self)

    def cardaction(self):
        if self.player.gameboard.rplayer.numtags:
            if self.player.checkdo(1, 0):
                self.player.gameboard.DoDamage(1, 'meat')
        else:
            self.tellplayer("Runner is not tagged")


class HedgeFund(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Hedge Fund"
        self.rezcost = 5
        self.subtype = "Transaction"
        self.cardtext = "Gain 9 credits"

    def cardaction(self):
        if OperationCard.InstallAction(self):
            self.player.numcredits += 9
            self.tellplayer("You gained 9 credits")


defaultcorpdeck = [PadCampaign, PadCampaign, PadCampaign, MiningCorp, MiningCorp, Hunter, Hunter, Enigma, Enigma,
                   Enigma, WallofStatic, WallofStatic, WallofStatic, PSF, PSF, PSF, PriorityRequisition,
                   PriorityRequisition, PriorityRequisition, HedgeFund, HedgeFund, HedgeFund]

#Haas-Biodroid Cards	
class ABT(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Accelerated Beta Test"
        self.agendapoints = 2
        self.advancetotal = 3
        self.subtype = 'Research'
        self.cardtext = "When you score Accelerated Beta Test, you may look at the top 3 cards of R&D.  If any of those cards are ice, you may install and rez them, ignoring all costs. Trash the rest of the cards you looked at."

    def ScoreAction(self):
        AgendaCard.ScoreAction(self)
        self.tellplayer("You will now draw 3 cards from R&D and install or trash them")
        for i in range(1, 4):
            self.player.drawcard(0)
            lastcard = self.player.hand.cards[-1]
            if lastcard.type == 'Ice':
                lastcard.readcard()
                lastcard.InstallAction(0)
                lastcard.RezAction()
            else:
                lastcard.trashaction(False)


class AdonisCampaign(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Adonis Campaign"
        self.subtype = "Advertisement"
        self.trashcost = 3
        self.rezcost = 4
        self.cardtext = "Place 12 Credits from the bank on Adonis Campaign when it is rezzed.  When there are no credits left on Adonis Campaign, trash it.  Take 3 credits from Adonis Campaign when your turn begins."

    def RezAction(self):
        self.currentpoints = 12
        self.takeaction = [self.player.takecredit, self.player.takecredit, self.player.takecredit, self.reup]
        for thing in self.takeaction:
            self.player.TurnStartActions.append(thing)

    def reup(self, azero):
        self.currentpoints -= 3
        self.tellplayer("THE POWER OF ADONIS CAMPAIGN GAVE YOU 3 CREDITS")
        self.tellplayer("(%d tokens left on Adonis Campaign)" % self.currentpoints)
        if not self.currentpoints:
            self.tellplayer("Trashing Adonis Campaign")
            self.trashaction(True)


class AggressiveSecretary(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Aggressive Secretary"
        self.subtype = "Ambush"
        self.rezcost = 0
        self.trashcost = 0
        self.advancetotal = 100
        self.cardtext = "Aggressive Secretary can be advanced. If you pay 2 credits when the Runner accesses Aggressive Secretary, trash 1 program for each advancement token on Aggressive Secretary."

    def RunnerAccessed(self):
        if self.currentpoints:
            self.tellplayer(self.readcard())
            self.tellplayer("There are %d tokens on Aggressive Secretary" % self.currentpoints)
            question = "CORP PLAYER: pay to activate Aggressive Secretary? > "
            if self.player.yesno(question) and self.player.checkdo(0, 2):
                for i in range(self.currentpoints):
                    self.player.trashsomething(3)


class BioticLabor(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Biotic Labor"
        self.rezcost = 4
        self.cardtext = "Gain 2 clicks"

    def cardaction(self):
        if OperationCard.InstallAction(self):
            self.player.numclicks += 2
            self.tellplayer("You gained 2 clicks")


class Shipment(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Shipment from Mirrormorph"
        self.rezcost = 1
        self.cardtext = "Immediately install up to 3 cards (spending no clicks but paying all install costs)"

    def cardaction(self):
        if OperationCard.InstallAction(self):
            i = 3
            while i:
                self.tellplayer(self.player.hand)
                self.tellplayer("choose a card (%d left): " % i)
                self.tellplayer("[type 'Cancel' if you can't play any]")
                x = self.player.asknum("card: ", 1, len(self.player.hand.cards) + 1)
                if x == 'cancel':
                    break
                else:
                    try:
                        self.player.hand.cards[x - 1].InstallAction(0)
                        i -= 1
                    except:
                        self.tellplayer("invalid card")


class ArchivedMemories(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Archived Memories"
        self.rezcost = 0
        self.cardtext = 'Add 1 card from Archives to HQ'

    def cardaction(self):
        self.tellplayer(self.player.archivepile)
        maxnum = len(self.player.archivepile.cards) + 1
        x = self.player.asknum("choose card> ", 1, maxnum + 1)
        if x == 'cancel': return False
        if self.InstallAction():
            chosencard = self.player.archivepile.cards[x - 1]
            self.player.archivepile.give(chosencard, self.player.hand)


class Troubleshooter(UpgradeCard):
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "Corporate Troubleshooter"
        self.rezcost = 0
        self.trashcost = 2
        self.subtype = "Connection"
        self.cardtext = "Pay X credits and trash this card: Choose a piece of rezzed ice protecting this server. That ice has +X strength until the end of the turn."
        self.chosencard = '<None>'

    def RezAction(self):
        self.player.playablecardlist.append(self)

    def cardaction(self):
        self.currentpoints = self.player.asknum("Choose # of credits: ", 1, self.player.numcredits + 1)
        if self.currentpoints == 'cancel':
            self.currentpoints = 0
            return False
        if self.player.checkdo(0, self.currentpoints):
            cardlist = []
            server = self.player.serverlist[self.installedin - 1]
            for i, ice in enumerate(server.Icelist.cards):
                if ice.faceup:
                    self.tellplayer("(" + str(len(cardlist) + 1) + ") " + str(ice))
                    cardlist.append(server.Icelist.cards[i])
            choice = self.player.asknum("Choose Ice to Enhance: ", 1, len(cardlist) + 1)
            if choice == 'cancel': return False
            self.chosencard = cardlist[choice - 1]
            self.chosencard.icestr += self.currentpoints
            self.player.TurnStartActions.append(self.reup)
            self.trashaction(True)

    def reup(self, azero):
        self.chosencard.icestr -= self.currentpoints
        self.player.TurnStartActions.remove(self.reup)


class ExpData(UpgradeCard):  #needs updating
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "Experiental Data"
        self.rezcost = 2
        self.trashcost = 2
        self.cardtext = "All ice protecting this server has +1 strength"

    def RezAction(self):
        for ice in self.player.serverlist[self.installedin - 1].Icelist.cards:
            ice.icestr += 1

    def trashaction(self, faceup, location=''):
        if self.installedin and self.faceup:
            for ice in self.player.serverlist[self.installedin - 1].Icelist.cards:
                ice.icestr -= 1
        corpcard.trashaction(self, faceup, location)


class Heimdall(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Heimdall 1.0"
        self.rezcost = 8
        self.icestr = 6
        self.subtype = "Barrier"
        self.cardtext = "The Runner can spend 1 click to break any subroutine on Heimdall 1.0. Subroutine1: Do 1 brain damage.  Subroutine2: End the run.  Subroutine3: End the run."
        self.subroutines = {1: ['Do 1 brain damage', True], 2: ['End the run', True], 3: ['End the run', True]}
        self.spendclickoption = True


class Ichi(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Ichi 1.0"
        self.rezcost = 5
        self.icestr = 4
        self.subtype = "Sentry"
        self.cardtext = "The Runner can spend 1 click to break any subroutine on Ichi 1.0.  Subroutine1: Trash 1 program.  Subroutine2: Trash 1 program.  Subroutine3: Trace1 - if successful, give the Runner 1 tag and do 1 brain damage."
        self.subroutines = {1: ['Trash 1 program', True], 2: ['Trash 1 program', True], 3: ['Trace 1 (extra)', True]}
        self.spendclickoption = True

    def ExtraAction(self):
        self.damage(1, 'brain')


class Rototurret(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Rototurret"
        self.rezcost = 4
        self.icestr = 0
        self.subtype = "Sentry"
        self.cardtext = "Subroutine1: Trash 1 program.  Subroutine2: End the run."
        self.subroutines = {1: ['Trash 1 program', True], 2: ['End the run', True]}


class Viktor(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Viktor 1.0"
        self.rezcost = 3
        self.icestr = 3
        self.subtype = "Code Gate"
        self.cardtext = "The Runner can spend 1 click to break any subroutine on Viktor 1.0.  Subroutine1: Do 1 brain damage.  Subroutine2: End the run."
        self.subroutines = {1: ['Do 1 brain damage', True], 2: ['End the run', True]}
        self.spendclickoption = True


HBdeck = [ABT, ABT, ABT, AdonisCampaign, AdonisCampaign, AdonisCampaign, AggressiveSecretary, AggressiveSecretary,
          BioticLabor, BioticLabor, BioticLabor, Shipment, Shipment, ArchivedMemories, ArchivedMemories, Troubleshooter,
          ExpData, ExpData, Heimdall, Heimdall, Ichi, Ichi, Ichi, Rototurret, Rototurret, Viktor, Viktor]


#NBN Cards
#2 recurring credits to be used during trace attempts.

class Psychographics(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Psychographics"
        self.rezcost = 0
        self.cardtext = "X is equal to or less than the number of tags the Runner has.  Place X advancement tokens on a card that can be advanced."

    def cardaction(self):
        tags = self.player.gameboard.rplayer.numtags
        self.tellplayer("Runner has %d tags" % tags)
        if not tags: return False
        x = self.player.asknum("> ", 0, tags + 1)
        if not x: return False
        self.rezcost = x
        if self.InstallAction():
            self.player.advancecard(0, x)


class SeaSource(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Sea Source"
        self.rezcost = 2
        self.cardtext = "Play only if the Runner made a successful run during his or her last turn.  Trace3 - If successful, give the Runner 1 tag"

    def cardaction(self):
        togs = False
        for thing in self.player.gameboards.rplayer.TurnSummary:
            if 'run' in thing: togs = True
        if not togs:
            self.tellplayer("Runner did not make a run last turn")
            return False
        if self.InstallAction():
            self.player.gameboard.StartTrace(3)


class ClosedAccounts(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Closed Accounts"
        self.rezcost = 1
        self.subtype = "Gray Ops"
        self.cardtext = "Play only if the Runner is tagged.  The Runner loses all credits in his or her credit pool"

    def cardaction(self):
        tags = self.player.gameboard.rplayer.numtags
        self.tellplayer("Runner has %d tags" % tags)
        if not tags: return False
        if self.InstallAction():
            self.player.gameboard.rplayer.numcredits = 0


class AnonymousTip(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Anonymous Tip"
        self.rezcost = 0
        self.cardtext = "Draw 3 cards"

    def cardaction(self):
        if self.InstallAction():
            self.trashaction()
            self.player.drawcard(0)
            self.player.drawcard(0)
            self.player.drawcard(0)


class RedHerrings(UpgradeCard):  #not done
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "Red Herrings"
        self.rezcost = 1
        self.trashcost = 1
        self.cardtext = "Each time the Runner accesses an agenda card from this server, he or she must pay 5 credits as an additional cost in order to steal it.  This applies even during the run on which the Runner trashes Red Herrings."


class SanSan(UpgradeCard):
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "SanSan City Guard"
        self.subtype = "Region"
        self.rezcost = 6
        self.trashcost = 5
        self.cardtext = "The advancement requirement of agendas installed in this server is lowered by 1.  Limit 1 region per server."

    def RezAction(self):
        for card in self.player.serverlist[self.installedin - 1].installed.cards:
            if card.type == 'Agenda':
                card.advancetotal -= 1

    def trashaction(self, faceup, location=''):
        if self.installedin and self.faceup:
            for card in self.player.serverlist[self.installedin - 1].installed.cards:
                if card.type == 'Agenda':
                    card.advancetotal += 1
        corpcard.trashaction(self, faceup, location)


class GhostBranch(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Ghost Branch"
        self.subtype = "Ambush - Facility"
        self.rezcost = 0
        self.trashcost = 0
        self.advancetotal = 100
        self.cardtext = "Ghost Branch can be advanced.  When the Runner accesses Ghost Branch, you may give the Runner 1 tag for each advancement token on Ghost Branch."

    def RunnerAccessed(self):
        if self.currentpoints:
            self.tellplayer(self.readcard())
            self.tellplayer("There are %d tokens on Ghost Branch" % self.currentpoints)
            self.tellplayer("Runner receives %d tags" % self.currentpoints)
            self.player.gameboard.rplayer.numtags += self.currentpoints


class BreakingNews(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Breaking News"
        self.advancetotal = 2
        self.agendapoints = 1
        self.cardtext = "When you score Breaking News, give the Runner 2 tags.  When the turn on which you scored Breaking News ends, the Runner loses 2 tags."

    def ScoreAction(self):
        AgendaCard.ScoreAction(self)
        self.player.gameboard.rplayer.numtags += 2
        self.player.TurnEndActions.append(self.turnend)

    def turnend(self):
        self.player.TurnEndActions.remove(self.turnend)
        self.player.gameboard.rplayer.numtages -= 2


class AstroScript(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "AstroScript Pilot Program"
        self.advancetotal = 3
        self.agendapoints = 2
        self.subtype = "Initiative"
        self.cardtext = "Place 1 agenda counter on AstroScript Pilot Program when you score it.  Hosted agenda counter: Place 1 advancement token on a card that can be advanced"

    def ScoreAction(self):
        self.player.playablecardlist.append(self)

    def cardaction(self):
        self.player.playablecardlist.remove(self)
        self.player.advancecard(0)


class MatrixAnalyzer(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Matrix Analyzer"
        self.rezcost = 1
        self.icestr = 3
        self.subtype = "Sentry - Tracer - Observer"
        self.cardtext = "When the Runner encounters Matrix Analyzer, you may pay 1 credit to place 1 advancement token on a card that can be advanced. Subroutine 1: Trace2 - If successful, give the Runner 1 tag"
        self.subroutines = {1: ['Trace 2', True]}

    def EncounterAction(self):
        question = "Pay 1 credit to advance a card? > "
        if self.player.yesno(question):
            self.player.advancecard()


class DataRaven(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Data Raven"
        self.rezcost = 4
        self.icestr = 4
        self.subtype = "Sentry - Tracer - Observer"
        self.cardtext = "When the Runner encounters Data Raven, he or she must either take 1 tag or end the run.  Hosted power counter: Give the Runner 1 tag. Subroutine1: Trace3 - If successful, place 1 power counter on Data Raven"
        self.subroutines = {1: ['Trace 3 (extra)', True]}

    def EncounterAction(self):
        self.tellplayer("Runner must either take 1 tag or end the run")
        if self.player.yesno("Take the tag? "):
            self.player.gameboard.rplayer.numtags += 1
        else:
            self.player.gameboard.winrun = False
        if self.currentpoints:
            self.tellplayer("Pay tokens off Data Raven to tag runner?")
            ans = self.player.asknum("> ", 0, self.currentpoints + 1)
            if ans:
                self.player.gameboard.rplayer.numtags += ans
                self.currentpoints -= ans

    def ExtraAction(self):
        self.tellplayer("Place 1 token on Data Raven")
        self.currentpoints += 1


class TollBooth(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Tollbooth"
        self.rezcost = 8
        self.icestr = 5
        self.subtype = "Code Gate"
        self.cardtext = "When the Runner encounters Tollbooth, he or she must pay 3 credits, if able.  If the Runner cannot pay 3 credits, end the run.  Subroutine1: End the run."
        self.subroutines = {1: ['End the run', True]}

    def EncounterAction(self):
        self.tellplayer("Runner must pay 3 credits or end the run")
        if self.player.yesno("Pay? ") and self.player.gameboard.rplayer.checkdo(0, 3):
            self.tellplayer("Ok, continue")
        else:
            self.player.gameboard.winrun = False


NBNdeck = [Psychographics, Psychographics, SeaSource, SeaSource, ClosedAccounts, ClosedAccounts, AnonymousTip,
           AnonymousTip, RedHerrings, RedHerrings, SanSan, GhostBranch, GhostBranch, GhostBranch, BreakingNews,
           BreakingNews, AstroScript, AstroScript, MatrixAnalyzer, MatrixAnalyzer, MatrixAnalyzer, DataRaven, DataRaven,
           DataRaven, TollBooth, TollBooth, TollBooth]

#Weyland Consortium Cards
#Gain 1 credits whenever you play a transaction operation

class Beanstalk(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Beanstalk Royalties"
        self.rezcost = 0
        self.subtype = "Transaction"
        self.cardtext = "Gain 3 credits"

    def cardaction(self):
        if self.InstallAction():
            self.player.numcredits += 3


class ShipmentfromK(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Shipment from Kaguya"
        self.rezcost = 0
        self.cardtext = "Place 1 advancement token on each of up to 2 different installed cards that can be advanced"

    def cardaction(self):
        if self.InstallAction():
            self.player.advancecard(0)
            self.tellplayer("(ok don't pick the same card again)")
            self.player.advancecard(0)


class AggressiveNegotiation(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Aggressive Negotiation"
        self.rezcost = 1
        self.cardtext = "Play only if you scored an agenda this turn.  Search R&D for 1 card and add it to HQ.  Shuffle R&D"

    def cardaction(self):
        togs = False
        for thing in self.player.TurnSummary:
            if 'Scored' in thing: togs = True
        if not togs:
            self.tellplayer("You haven't scored an agenda this turn")
            return False
        if not self.InstallAction(): return False
        for i, card in enumerate(self.player.deck.cards):
            self.tellplayer("(" + str(i + 1) + ") " + str(card))
        choice = self.player.asknum("Choose card: ", 1, len(self.player.deck.cards) + 1)
        if choice == 'cancel': return False
        chosencard = self.player.deck.cards[choice - 1]
        self.player.deck.give(chosencard, self.player.hand)
        self.player.deck.shuffle()


class ScorchedEarth(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Scorched Earth"
        self.rezcost = 3
        self.subtype = "Black Ops"
        self.cardtext = "Play only if the Runner is tagged. Do 4 meat damage"


class ResearchStation(UpgradeCard):
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "Reseaerch Station"
        self.rezcost = 2
        self.trashcost = 3
        self.subtype = "Facility"
        self.cardtext = "Install only in the root of HQ.  Your maximum hand size is +2"


class SecuritySub(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Security Subcontract"
        self.subtype = "Transaction"
        self.rezcost = 0
        self.trashcost = 3
        self.cardtext = "Pay 1 click and trash a rezzed piece of ice: Gain 4 credits"


class HostileTakeover(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Hostile Takeover"
        self.subtype = "Expansion"
        self.agendapoints = 1
        self.advancetotal = 2
        self.cardtext = "When you score Hostile Takeover, gain 7 credits and take 1 bad publicity"


class PostedBounty(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Posted Bounty"
        self.subtype = "Security"
        self.agendapoints = 1
        self.advancetotal = 3
        self.cardtext = "When you score Posted Bounty, you may forfeit it to give the Runner 1 tag and take 1 bad publicity"


class IceWall(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Ice Wall"
        self.subtype = "Barrier"
        self.rezcost = 1
        self.icestr = 1
        self.advancetotal = 100
        self.cardtext = "Ice Wall can be advanced and has +1 strength for each advancement token on it.  Subroutine1: End the run"
        self.subroutines = {1: ['End the run', True]}


class Shadow(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Shadow"
        self.subtype = "Sentry - Tracer"
        self.rezcost = 3
        self.icestr = 1
        self.cardtext = "Shadow can be advanced and has +1 strength for each advancement token on it. Subroutine1: The Corp gains 2 credits. Subroutine2: Trace 3 - If successful, give the Runner 1 tag"
        self.subroutines = {1: ['Corp 2 Credits', True], 2: ['Trace 3', True]}


class Archer(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Archer"
        self.subtype = "Sentry - Destroyer"
        self.rezcost = 4
        self.icestr = 6
        self.cardtext = "As an additional cost to rez Archer, the Corp must forfeit an agenda.  Subroutine1: The Corp gains 2 credits. Subroutine2: Trash 1 program. Subroutine3: Trash 1 program. Subroutine4: End the run."
        self.subroutines = {1: ['Corp 2 Creidts', True], 2: ['Trash 1 program', True], 3: ['Trash 1 program', True],
                            4: ['End the run', True]}


class Hadrian(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Hadrian's Wall"
        self.subtype = "Barrier"
        self.rezcost = 10
        self.icestr = 7
        self.advancetotal = 100
        self.cardtext = "Hadrian's Wall can be advanced and has +1 strength for each advancement token on it.  Subroutine1: End the run.  Subroutine2: End the run"
        self.subroutines = {1: ['End the run', True], 2: ['End the run', True]}


WCdeck = [Beanstalk, Beanstalk, Beanstalk, ShipmentfromK, ShipmentfromK, AggressiveNegotiation, AggressiveNegotiation,
          ScorchedEarth, ScorchedEarth, ResearchStation, ResearchStation, SecuritySub, HostileTakeover, HostileTakeover,
          HostileTakeover, PostedBounty, PostedBounty, IceWall, IceWall, IceWall, Shadow, Shadow, Shadow, Archer,
          Archer, Hadrian, Hadrian]

#Jinteki Cards
#Whenever an agenda is scored or stolen, do 1 net damage

class NeuralEMP(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Neural EMP"
        self.subtype = "Gray Ops"
        self.rezcost = 2
        self.cardtext = "Play only if the Runner made a run during his or her last turn.  Do 1 net damage"


class Precognition(OperationCard):
    def __init__(self):
        OperationCard.__init__(self)
        self.name = "Precognition"
        self.rezcost = 0
        self.cardtext = "Look at the top 5 cards of R&D and arrange them in any order"


class Akitaro(UpgradeCard):
    def __init__(self):
        UpgradeCard.__init__(self)
        self.name = "Akitaro Watanabe"
        self.rezcost = 1
        self.trashcost = 3
        self.subtype = "Sysop - Unorthodox"
        self.cardtext = "The rez cost of ice protecting this server is lowered by 2"


class Snare(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Snare!"
        self.subtype = "Ambush"
        self.rezcost = 0
        self.trashcost = 0
        self.cardtext = "If Snare! is accessed from R&D, the Runner must reveal it.  If you pay 4 credits when the Runner accesses Snare!, do 3 net damage and give the Runner 1 tag.  Ignore this effect if the Runner accesses Snare from Archives."


class Zaibatsu(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Zaibatsu Loyalty"
        self.rezcost = 0
        self.trashcost = 4
        self.cardtext = "If the Runner is about to expose a card, you may rez Zaibatsu Loyalty.  1 credit or trash this card: Prevent 1 card from being exposed."


class Junebug(AssetCard):
    def __init__(self):
        AssetCard.__init__(self)
        self.name = "Project Junebug"
        self.rezcost = 0
        self.trashcost = 0
        self.cardtext = "Project Junebug can be advanced.  If you pay 1 credit when th eRunner accesses Project Junebug, do 2 net damage for each advancement token on Project Junebug"


class Nisei(AgendaCard):
    def __init__(self):
        AgendaCard.__init__(self)
        self.name = "Nisei MK II"
        self.subtype = "Initiative"
        self.agendapoints = 2
        self.advancetotal = 4
        self.cardtext = "Place 1 agenda counter on Nisei MK II when you score it.  Hosted agenda counter: End the run"


class DataMine(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Data Mine"
        self.subtype = "Trap - AP"
        self.rezcost = 0
        self.icestr = 2
        self.cardtext = "Subroutine1: Do 1 net damage. Trash Data Mine"
        self.subroutines = {1: ['Do 1 trash', True]}


class Chum(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Chum"
        self.subtype = "Code Gate"
        self.rezcost = 1
        self.icestr = 4
        self.cardtext = "Subroutine1: The next piece of ice the Runner encounters during this run has +2 strength.  Do 3 net damage unless the Runner breaks all subroutines on that piece of ice"


class NeuralKatana(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Neural Katana"
        self.subtype = "Sentry - AP"
        self.rezcost = 4
        self.icestr = 3
        self.cardtext = "Subroutine1: Do 3 net damage"


class CellPortal(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Cell Portal"
        self.subtype = "Code Gate - Deflector"
        self.rezcost = 5
        self.icestr = 7
        self.cardtext = "Subroutine1: The Runner approaches the outermost piece of ice protecting the attacked server.  Derez Cell Portal"


class WallofThorns(IceCard):
    def __init__(self):
        IceCard.__init__(self)
        self.name = "Wall of Thorns"
        self.subtype = "Barrier - AP"
        self.rezcost = 8
        self.icestr = 5
        self.cardtext = "Subroutine1: Do 2 net damage. Subroutine2: End the run"


Jdeck = [NeuralEMP, NeuralEMP, Precognition, Precognition, Akitaro, Snare, Snare, Snare, Zaibatsu, Junebug, Junebug,
         Junebug, Nisei, Nisei, Nisei, DataMine, DataMine, Chum, Chum, NeuralKatana, NeuralKatana, NeuralKatana,
         CellPortal, CellPortal, WallofThorns, WallofThorns, WallofThorns]

#===================================================
#  BEGIN INDIVIDUAL R-CARD DEFINITIONS 
#===================================================


#Default Runner Deck Cards
class Armitage(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Armitage Codebusting"
        self.subtype = "Job"
        self.rezcost = 1
        self.cardtext = "Place 12 credits from the bank on Armitage Codebusting when it is installed.  When there are no credits left on Armitage Codebusting, trash it.  1 click: Take 2 credits from Armitage Codebusting"

    def RezAction(self):
        self.player.playablecardlist.append(self)
        self.currentpoints = 12
        self.rezcost = 0

    def cardaction(self):
        if self.player.checkdo(1, 0):
            self.player.numcredits += 2
            self.currentpoints -= 2
            self.tellplayer("You gained 2 credits")
            self.tellplayer("(%d credits left on Armitage Codebusting)" % self.currentpoints)
            if not self.currentpoints:
                self.trashaction()


class Globalsec(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Access to Globalsec"
        self.subtype = "Link"
        self.rezcost = 1
        self.cardtext = "+1 Link"

    def RezAction(self):
        self.player.numlinks += 1
        self.tellplayer("You gained 1 Link")

    def trashaction(self):
        if self.installedin:
            self.player.numlinks -= 1
        runnercard.trashaction(self)


class SureGamble(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Sure Gamble"
        self.rezcost = 5
        self.cardtext = "Gain 9 credits"

    def cardaction(self):
        if self.player.checkdo(1, self.rezcost):
            self.player.numcredits += 9
            self.tellplayer("You gained 9 credits")
            self.trashaction()


class Infiltration(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Infiltration"
        self.rezcost = 0
        self.cardtext = "Gain 2 credits or expose 1 card"

    def cardaction(self):
        if self.player.checkdo(1, self.rezcost):
            self.tellplayer("Your choices: \n\t (1) Gain 2 credits \n\t (2) Expose 1 card")
            choice = self.player.asknum("You choose: ", 1, 3)
            if choice == 1:
                self.player.numcredits += 2
                self.tellplayer("Gained 2 credits")
            elif choice == 2:
                self.tellplayer("expose 1 card (todo)")
            else:
                self.tellplayer("that's not a choice....")
            self.trashaction()


class Crypsis(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Crypsis"
        self.subtype = "Icebreaker - Virus"
        self.rezcost = 5
        self.programcost = 1
        self.icestr = 1
        self.cardtext = "1 credit: Break ice subroutine. 1 credit: +1 strength. 1 click: Place 1 virus counter on Crypsis.  When an encounter with a piece of ice in which you used Crypsis to break a subroutine ends, remove 1 hosted virus counter or trash Cyrpsis"

    def RezAction(self):
        self.player.playablecardlist.append(self)

    def cardaction(self):
        if self.player.checkdo(1, 0):
            self.currentpoints += 1

    def breakaction(self, ice):
        self.IBincreasestr(ice)
        if ice.icestr <= self.icestr:
            s = 1
            while s:
                self.tellplayer("Pay 1 credit to break 1 subroutine")
                ice.printsubroutines()
                s = self.player.asknum("Break which subroutines (0 for done): ", 0, len(ice.subroutines) + 1)
                if s and ice.subroutines[s][1] and self.player.checkdo(0, 1):
                    ice.subroutines[s][1] = False
            self.icestr = 1
            if self.currentpoints:
                self.currentpoints -= 1
            else:
                self.trashaction()
        return False


shortdeck = [Armitage, Globalsec, SureGamble, Infiltration, Crypsis]
defaultrunnerdeck = shortdeck + shortdeck + shortdeck

#Kate McCaffrey (Natural) Cards
class Toolbox(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "The Toolbox"
        self.rezcost = 9
        self.subtype = "Console"
        self.cardtext = "+2 Program Limit. +2 Link. 2 Recurring Credits, to be used to pay for icebreakers.  Limit 1 console per player."
        self.savenum = 0
        self.takeaction = [self.Reset]

    def RezAction(self):
        self.tellplayer("Program Limit +2, Link +2")
        self.player.programlimit += 2
        self.player.numlinks += 2
        self.currentpoints = 2
        self.player.TurnStartActions.append(*self.takeaction)

    def breakaction(self, someice):
        if self.currentpoints:
            self.tellplayer("Take 2 credits for ice breaking")
            self.savenum = self.player.numcredits
            self.player.numcredits += 2
            self.currentpoints -= 2
        else:
            self.tellplayer("No credits on Toolbox to use!")

    def Reset(self, azero):
        if self.currentpoints < 2:
            self.tellplayer("Putting 2 credits back on Toolbox")
            self.currentpoints = 2
            if self.player.numcredits >= self.savenum:
                self.tellplayer("You have more credits now than when you started last run...")
                self.tellplayer("Resetting to previous number of " + self.savenum)
                self.player.numcredits = self.savenum


class Akamatsu(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Akamatsu Mem Chip"
        self.rezcost = 1
        self.cardtext = "+1 Program Limit"
        self.subtype = "Chip"

    def RezAction(self):
        self.tellplayer("Program Limit +1")
        self.player.programlimit += 1

    def trashaction(self):
        if self.installedin:
            self.player.programlimit -= 1
            self.tellplayer("Program Limit -1")
        runnercard.trashaction(self)


class PersonalTouch(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "The Personal Touch"
        self.subtype = "Mod"
        self.rezcost = 2
        self.cardtext = "Install The Personal Touch only on an icebreaker.  Hosted icebreaker has +1 strength"

    def RezAction(self):
        self.player.TurnStartActions.append(self.reup)
        gk = 1
        while gk:
            chosencard = self.player.choosefromboard()
            if 'Icebreaker' in chosencard.subtype:
                chosencard.icestr += 1
                self.installedin = chosencard
                gk = 0
            else:
                self.tellplayer("fail!")

    def trashaction(self):
        if self.installedin:
            self.installedin.icestr -= 1
        runnercard.trashaction(self)

    def reup(self, azero):
        if not self.installedin.installedin:
            self.trashaction(False)
            self.player.TurnStartActions.remove(self.reup)


class RabbitHole(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Rabbit Hole"
        self.subtype = "Link"
        self.rezcost = 2
        self.cardtext = "+1 Link.  When Rabbit Hole is installed, you may search your stack for another copy of Rabbit Hole and install it by paying its install cost.  Shuffle your stack."

    def RezAction(self):
        self.tellplayer("Link Strength +1")
        self.player.numlinks += 1
        indeck = False
        for card in self.player.deck.cards:
            if card.name == "Rabbit Hole":
                self.tellplayer("Found another copy of Rabbit Hole in the stack.")
                if self.player.yesno("Install? ") and self.player.checkdo(0, 2):
                    self.player.deck.give(card, self.player.boardhand)
                    self.player.numlinks += 1
                indeck = True
        if not indeck:
            self.tellplayer("Can't find Rabbit Hole in stack")

    def trashaction(self):
        if self.installedin:
            self.player.numlinks -= 1
            self.tellplayer("Number of Links -1")
        runnercard.trashaction(self)


class Diesel(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Diesel"
        self.rezcost = 0
        self.cardtext = "Draw 3 cards"

    def cardaction(self):
        if self.player.checkdo(1, self.rezcost):
            self.trashaction()
            self.player.drawcard(0)
            self.player.drawcard(0)
            self.player.drawcard(0)


class Sacrificial(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Sacrificial Construct"
        self.subtype = "Remote"
        self.rezcost = 0
        self.cardtext = "Trash this card: Prevent an installed program or an installed piece of hardware from being trashed"

    def RezAction(self):
        self.player.preventset[self] = 'trash'

    def cardaction(self):
        if self.installedin:
            del self.player.preventset[self]
        self.trashaction()
        return True


class Modded(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Modded"
        self.subtype = "Mod"
        self.rezcost = 0
        self.cardtext = "Install a program or a piece of hardware, lowering the install cost by 3"

    def cardaction(self):
        if self.player.checkdo(0, self.rezcost):
            self.tellplayer(self.cardtext)
            self.player.showopts("hand")
            choice = self.player.asknum("Install: ", 1, len(self.player.hand.cards) + 1)
            while choice != 'cancel':
                chosencard = self.player.hand.cards[choice - 1]
                if chosencard.type in ['Program', 'Hardware']:
                    chosencard.rezcost = max(chosencard.rezcost - 3, 0)
                    if chosencard.InstallAction():
                        self.trashaction()
                    return True


class Aesops(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Aesop's Pawnshop"
        self.subtype = "Location - Connection"
        self.rezcost = 1
        self.cardtext = "When your turn begins, you may trash another of your installed cards to gain 3 credits"

    def RezAction(self):
        self.player.playablecardlist.append(self)

    def cardaction(self):
        if self.player.numclicks == 4:
            chosencard = self.player.choosefromboard()
            if chosencard:
                chosencard.trashaction()
                self.tellplayer("Gained 3 credits")
                self.player.numcredits += 3
        else:
            self.tellplayer("Cannot play this now")


class Tinkering(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Tinkering"
        self.subtype = "Mod"
        self.rezcost = 0
        self.cardtext = "Choose a piece of ice.  That ice gains sentry, code gate, and barrier until the end of the turn"

    def cardaction(self):
        if self.player.checkdo(1, self.rezcost):
            self.player.gameboard.ShowOpponent('runner')
            cardlist = []
            for server in self.player.gameboard.cplayer.serverlist:
                for ice in server.Icelist.cards:
                    cardlist.append(ice)
            for i, card in enumerate(cardlist):
                location = self.player.gameboard.cplayer.serverlist[card.installedin - 1].name
                if card.faceup:
                    self.tellplayer("(" + str(i + 1) + ") " + str(card) + " ---> in " + location)
                else:
                    self.tellplayer("(" + str(i + 1) + ") --A facedown Ice-- ---> in" + location)
            choice = self.player.asknum("Choosecard: ", 1, len(cardlist) + 1)
            if choice == 'cancel': return False
            chosencard = cardlist[choice - 1]
            chosencard.subtype += " - Sentry Code Gate Barrier -"
            self.installedin = chosencard
            self.player.TurnEndActions.append(self.turnend)

    def turnend(self):
        self.installedin.subtype.replace(" - Sentry Code Gate Barrier -", "")
        self.trashaction()


class MakersEye(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "The Maker's Eye"
        self.rezcost = 2
        self.subtype = "Run"
        self.cardtext = "Make a run on R&D.  If successful, access 2 additional cards from R&D"

    def cardaction(self):
        if self.player.checkdo(1, self.rezcost) and self.player.gameboard.StartRun(2):
            self.player.turnsummary.append('    -> Card effect made a run')
            self.player.gameboard.AccessCards(2, 3)
            for card in self.player.usedcardslist:
                card.Reset()
            self.trashaction()


class MagnumOpus(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Magnum Opus"
        self.rezcost = 5
        self.programcost = 2
        self.cardtext = "1 click: Gain 2 credits"

    def RezAction(self):
        self.player.playablecardlist.append(self)

    def cardaction(self):
        if self.player.checkdo(1, 0):
            self.player.numcredits += 2
            self.tellplayer("You gained 2 credits")


class GordianBlade(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Gordian Blade"
        self.subtype = "Icebreaker - Decoder"
        self.rezcost = 4
        self.programcost = 1
        self.icestr = 2
        self.cardtext = "1 credit: Break code gate subroutine.  1 credit: +1 strength for the remainder of this run"

    def breakaction(self, ice):
        if not self.IBtypecheck('Code Gate', ice): return False
        self.IBincreasestr(ice)
        if self.icestr >= ice.icestr:
            self.tellplayer("Pay 1 credit to break 1 Code Gate subroutine")
            if self.player.checkdo(0, 1):
                return True

    def Reset(self):
        self.icestr = 2


class NetShield(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Net Shield"
        self.rezcost = 2
        self.programcost = 1
        self.cardtext = "1 credit: Prevent the first net damage this turn"
        self.takeaction = [self.reup]

    def RezAction(self):
        self.player.preventset[self] = 'netdamage'

    def cardaction(self):
        if not self.currentpoints and self.player.checkdo(0, 1):
            self.tellplayer("Prevented 1 net damage")
            self.currentpoints += 1
            self.player.TurnStartActions.append(*self.takeaction)
            return True

    def reup(self, azero):
        self.currentpoints = 0
        self.player.TurnStartActions.remove(*self.takeaction)


class BatteringRam(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Battering Ram"
        self.subtype = "Icebreaker - Fracter"
        self.rezcost = 5
        self.programcost = 2
        self.icestr = 3
        self.cardtext = "2 credits: Break up to 2 barrier subroutines.  1 credit: +1 strength for the remainder of this run"

    def breakaction(self, ice):
        if not self.IBtypecheck('Barrier', ice): return False
        self.IBincreasestr(ice)
        if self.icestr >= ice.icestr:
            self.tellplayer("Pay 2 credits to break 2 Barrier subroutines")
            if self.player.checkdo(0, 2):
                s = 1
                n = 2
                while s and n:
                    ice.printsubroutines()
                    s = self.player.asknum("Break which subroutines (0 for done): ", 0, len(ice.subroutines) + 1)
                    if s and ice.subroutines[s][1]:
                        ice.subroutines[s][1] = False
                        n -= 1
        return False

    def Reset(self):
        self.icestr = 3


class PipeLine(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Pipeline"
        self.subtype = "Icebreaker - Killer"
        self.rezcost = 3
        self.programcost = 1
        self.icestr = 1
        self.cardtext = "1 credit: Break sentry subroutine. 2 credits: +1 strength for the remainder of this run."

    def breakaction(self, ice):
        if not self.IBtypecheck('Sentry', ice): return False
        self.IBincreasestr(ice, 2)
        if self.icestr >= ice.icestr:
            self.tellplayer("Pay 1 credit to break 1 Sentry subroutine")
            if self.player.checkdo(0, 1):
                return True

    def Reset(self):
        self.icestr = 1


naturaldeck = [Toolbox, Akamatsu, Akamatsu, PersonalTouch, PersonalTouch, RabbitHole, RabbitHole, Diesel, Diesel,
               Diesel, Sacrificial, Sacrificial, Modded, Modded, Aesops, Tinkering, Tinkering, Tinkering, MakersEye,
               MakersEye, MakersEye, MagnumOpus, MagnumOpus, GordianBlade, GordianBlade, GordianBlade, NetShield,
               NetShield, BatteringRam, BatteringRam, PipeLine, PipeLine]

#Gabiel Santiago (cyborg) cards
#the first time you make a successful run on HQ each turn gain 2 credits
class DataDealer(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Data Dealer"
        self.subtype = "Connection - Seedy"
        self.rezcost = 0
        self.cardtext = "Forfeit an agenda, pay 1 click: Gain 9 credits"

    def cardaction(self):
        if self.player.ScoredCards:
            for i, card in enumerate(self.player.ScoredCards):
                self.tellplayer(" (" + str(i + 1) + ") " + str(card))
            self.tellplayer("Forfeit an agenda?")
            choice = self.player.asknum("> ", 1, len(self.player.ScoredCards) + 1)
            if choice == 'cancel': return False
            if self.player.checkdo(1, 0):
                chosencard = self.player.ScoredCards[choice - 1]
                self.tellplayer("Forfeited " + str(chosencard) + ", gained 9 credits")
                self.player.ScoredCards.remove(chosencard)
                self.player.numcredits += 9
        else:
            self.tellplayer("No Agendas to forfeit!")


class BankJob(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Bank Job"
        self.subtype = "Job"
        self.rezcost = 1
        self.cardtext = "Place 8 credits from the bank on Back Job when it is installed.  When there are no credits left on Bank Job, trash it.  Whenever you make a successful run on a remote server, instead of accessing cards, you may take any number of credits from Bank Job"


class AccountSiphon(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Account Siphon"
        self.subtype = "Run - Sabotage"
        self.rezcost = 0
        self.cardtext = "Make a run on HQ.  If successful, instead of accessing cards you may force the Corp to lose up to 5 credits, then you gain 2 credits for each credit lost and take 2 tags."


class SpecialOrder(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Special Order"
        self.rezcost = 1
        self.cardtext = "Search your stack for an icebreaker, reveal it, and add it to your grip.  Shuffle your stack"


class InsideJob(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Inside Job"
        self.subtype = "Run"
        self.rezcost = 2
        self.cardtext = "Make a run.  Bypass the first piece of ice encountered during this run"


class EasyMark(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Easy Mark"
        self.subtype = "Job"
        self.rezcost = 0
        self.cardtext = "Gain 3 credits"


class ForgedOrders(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Forged Activation Orders"
        self.subtype = "Sabotage"
        self.rezcost = 1
        self.cardtext = "Choose and unrezzed piece of ice.  The Corp must either rez that ice or trash it"


class Lemuria(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Lemuria Codecracker"
        self.rezcost = 1
        self.cardtext = "1 click, 1 credit: Expose 1 card.  Use this ability only if you have made a successful run on HQ this turn"


class Desperado(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Desperado"
        self.subtype = "Console"
        self.rezcost = 3
        self.cardtext = "+1 Memory, Gain 1 credit whenever you make a successful run.  Limit 1 console per player"


class Decoy(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Decoy"
        self.subtype = "Connection"
        self.rezcost = 1
        self.cardtext = "Trash: Avoid receiving 1 tag"


class CrashSpace(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Crash Space"
        self.subtype = "Location"
        self.rezcost = 2
        self.cardtext = "2 recurring credits to be used for removing tags. Trash: Prevent up to 3 meat damage"


class Ninja(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Ninja"
        self.subtype = "Icebreaker - Killler"
        self.rezcost = 4
        self.programcost = 1
        self.icestr = 0
        self.cardtext = "1 credit: Break sentry subroutine. 3 credits: +5 strength"


class Sneakdoor(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Sneakdoor Beta"
        self.rezcost = 4
        self.programcost = 2
        self.cardtext = "1 click: Make a run on Archives. If successful, instead treat it as a successful run on HQ"


class Aurora(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Aurora"
        self.subtype = "Icebreaker - Fracter"
        self.rezcost = 3
        self.programcost = 1
        self.icestr = 1
        self.cardtext = "2 credits: Break barrier subroutine. 2 credits: +3 strength"


class FemmeFatale(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Femme Fatale"
        self.subtype = "Icebreaker - Killer"
        self.rezcost = 9
        self.programcost = 1
        self.icestr = 2
        self.cardtext = "1 credit: Break sentry subroutine. 2 credits: +1 strength. When you install Femme Fatale, choose an installed piece of ice.  When you encounter that ice, you may spend 1 creidt per subroutine on that ice to bypass it."


cyborgdeck = [DataDealer, BankJob, BankJob, AccountSiphon, AccountSiphon, SpecialOrder, SpecialOrder, SpecialOrder,
              InsideJob, InsideJob, InsideJob, EasyMark, EasyMark, EasyMark, ForgedOrders, ForgedOrders, ForgedOrders,
              Lemuria, Lemuria, Desperado, Decoy, Decoy, CrashSpace, CrashSpace, Ninja, Ninja, Sneakdoor, Sneakdoor,
              Aurora, Aurora, FemmeFatale, FemmeFatale]

#Noise (G-mod) Cards
#whenever you install a virus program, the corp trashes the top card of R&D
class Grimoire(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Grimoire"
        self.subtype = "Console"
        self.rezcost = 3
        self.cardtext = "+2 Memory Limit, Whenever you install a virus program, place 1 virus counter on that program. Limit 1 console per player"


class Cyberfeeder(HardwareCard):
    def __init__(self):
        HardwareCard.__init__(self)
        self.name = "Cyberfeeder"
        self.subtype = "Chip"
        self.rezcost = 2
        self.cardtext = "1 recurring credit to be used for paying for icebreakers or installed virus programs"


class IceCarver(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Ice Carver"
        self.subtype = "Virtual"
        self.rezcost = 3
        self.cardtext = "All ice is encountered with its strength lowered by 1"


class Wyldside(ResourceCard):
    def __init__(self):
        ResourceCard.__init__(self)
        self.name = "Wyldside"
        self.subtype = "Location - Seedy"
        self.rezcost = 3
        self.cardtext = "When your turn begins, draw 2 cards and lose 1 click"


class DejaVu(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Deja Vu"
        self.rezcost = 2
        self.cardtext = "Add 1 card (or up to 2 virus cards) from your heap to your grip"


class DemolitionRun(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Demolition Run"
        self.subtype = "Run - Sabotage"
        self.rezcost = 2
        self.cardtext = "Make a run on HQ or R&D.  You may trash, at no cost, any cards you access (even if the cards cannot normally be trashed)"


class Stimhack(EventCard):
    def __init__(self):
        EventCard.__init__(self)
        self.name = "Stimhack"
        self.subtype = "Run"
        self.rezcost = 0
        self.cardtext = "Make a run, and gain 9 credits, which you may use only during this run.  After the run is completed, suffer 1 brain damage (cannot be prevented) and return to the bank any of the 9 credits not spent."


class Datasucker(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Datasucker"
        self.subtype = "Virus"
        self.rezcost = 1
        self.programcost = 1
        self.cardtext = "Whenever you make a successful run on a central server, place 1 virus counter on Datasucker. Hosted virus counter: Rezzed piece of ice currently being encountered has -1 strneght until the end of the encounter."


class Wyrm(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Wyrm"
        self.subtype = "Icebreaker - AI"
        self.rezcost = 1
        self.programcost = 1
        self.icestr = 1
        self.cardtext = "3 credits: Break ice subroutine on a piece of ice with 0 or less strength. 1 credit: Ice has -1 strength. 1 credit = +1 strength."


class Parasite(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Parasite"
        self.subtype = "Virus"
        self.rezcost = 2
        self.programcost = 1
        self.cardtext = "Install Parasite only on a rezzed piece of ice. Host ice has -1 strength for each virus counter on Parasite and is trashed if its strength is 0 or less.  When your turn begins, place 1 virus counter on Parasite"


class Corroder(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Corroder"
        self.name = "Icebreaker - Fracter"
        self.rezcost = 2
        self.programcost = 1
        self.icestr = 2
        self.cardtext = "1 credit: Break barrier subroutine. 1 credit: +1 strength"


class Djinn(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Djinn"
        self.subtype = "Daemon"
        self.rezcost = 2
        self.programcost = 1
        self.cardtext = "Djinn can host up to 3 memory units of non-icebreaker programs. The memory costs of hosted programs do not count against your memory limit. 1 click, 1 credit: Search your stack for a virus program, reveal it, and add it to your grip. Shuffle your stack."


class Medium(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Medium"
        self.subtype = "Virus"
        self.rezcost = 3
        self.programcost = 1
        self.cardtext = "Whenever you make a successful run on R&D, place 1 virus counter on Medium. Each virus counter after the first on Medium allows you to access 1 additional card from R&D whenever you access cards from R&D"


class Mimic(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Mimic"
        self.subtype = "Icebreaker - Killer"
        self.rezcost = 3
        self.programcost = 1
        self.icestr = 3
        self.cardtext = "1 credit: Break sentry subroutine"


class Yog(ProgramCard):
    def __init__(self):
        ProgramCard.__init__(self)
        self.name = "Yog.0"
        self.subtype = "Icebreaker - Decoder"
        self.rezcost = 5
        self.programcost = 1
        self.icestr = 3
        self.cardtext = "0 credits: Break code gate subroutine"


noisedeck = [Grimoire, Cyberfeeder, Cyberfeeder, Cyberfeeder, IceCarver, Wyldside, Wyldside, DejaVu, DejaVu,
             DemolitionRun, DemolitionRun, DemolitionRun, Stimhack, Stimhack, Stimhack, Datasucker, Datasucker, Wyrm,
             Wyrm, Parasite, Parasite, Parasite, Corroder, Corroder, Djinn, Djinn, Medium, Medium, Mimic, Mimic, Yog,
             Yog]