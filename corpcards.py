import gamemods

class corpcard(object):
	def __init__(self):
		self.name = '<None>'
		self.rezcost='<None>'
		self.type= '<None>'
		self.subtype='<No Subtype>'
		self.cardtext='<None>'
		self.trashcost='<None>'
		self.icestr='<None>'
		self.agendapoints='<None>'
		self.advancetotal= 0
		self.faceup = True
		self.currentpoints = 0
		self.takeaction = []
		self.installedin = 0
		self.player = ''
		self.id = '<None>'
		
	def __str__(self):
		reply = self.name + " (" + self.type +": " + self.subtype + ")"
		return reply
	
	def readcard(self):
		print "----- Card Name = %s -------" %self.name
		print "| Card Type = %s:%s" %(self.type,self.subtype)
		if self.type == 'Ice':
			print "| Ice Strength = " + str(self.icestr)
		elif self.type == 'Agenda':
			print "| Advancement Points needed = " + str(self.advancetotal)
			print "| Agenda Points = " + str(self.agendapoints)
		elif self.type == 'Operation':
			pass
		else:
			print "| Trash Cost = " +str(self.trashcost)
		print "| Rez Cost = " + str(self.rezcost)
		print "| Card Text = " + self.cardtext
		print "| Card ID# = " + str(self.id)
			
	def InstallAction(self, clickcost=1, x=0):
		creditcost = 0
		reply = False
		self.player.showopts("board")
		printout = ''
		for i,server in enumerate(self.player.serverlist):
			printout += "\n\t ("+str(i+1)+") " +str(server)
		printout += "\n\t ("+str(i+2)+") New Remote Server"
		print printout
		maxnum = len(self.player.serverlist)+1
		if not x:
			x=gamemods.ask_number("Choose Server to Install Card in: ",1, maxnum+1)
			if not x: return False
		if x == maxnum:
			self.player.serverlist.append(gamemods.remoteserver(x-3))
			print "creating new remote server %s" %self.player.serverlist[maxnum-1].name
		chosenserver = self.player.serverlist[x-1]
		installhand = chosenserver.installed
		if self.type in ['Asset', 'Agenda']:
			if chosenserver.MoreRoomForCards:
				chosenserver.MoreRoomForCards = False
			else:
				print "No more room for this type of card in this server"
				return False
		elif self.type == 'Ice':
			for icecard in chosenserver.Icelist.cards:
				creditcost += 1
			installhand = chosenserver.Icelist
		if self.player.checkdo(clickcost,creditcost):
			self.player.hand.give(self, installhand)
			self.faceup = False
			self.installedin = x		
			print "Installed %s on server: %s" %(self.name, chosenserver.name)
			self.player.turnsummary.append('Installed a card in '+str(chosenserver.name))
			reply = True
			if self.player.identity == 'HB' and self.player.firstcall:
				self.player.firstcall = False
				print "HB Power: Gain 1 credit"
				self.player.takecredit(0)
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
				cardlocation = self.player.serverlist[self.installedin-1].Icelist
			else:
				cardlocation = self.player.serverlist[self.installedin-1].installed
		else:
			cardlocation = self.player.hand
		if self.installedin and self.type != 'Ice':	
			self.player.serverlist[self.installedin-1].MoreRoomForCards = True
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
		self.player.turnsummary.append('Trashed ' +carddesc)
		print "Trashed " + str(self)
		
class IceCard(corpcard):
	def __init__(self):
		corpcard.__init__(self)
		self.type = 'Ice'
		self.subroutines = {} #{number: [name, unbroken]}
		self.spendclickoption = False
		
	def printsubroutines(self):
		reply = ''
		if self.subroutines:
			for id in self.subroutines.keys():
				reply += "\n\t Subroutine"+str(id)+": "+self.subroutines[id][0]
				if self.subroutines[id][1]:
					reply += "   [=== UNBROKEN ===]"
				else: 
					reply += "   [=== BROKEN ===]"
		else:
			reply = '<No Subroutines>'
		print reply + '\n'
		
	def RezAction(self):
		self.faceup = True
		
	def EncounterAction(self):
		pass
		
	def EndRun(self, opt='', opt2=''):
		self.player.gameboard.winrun = False
		
	def InitTrace(self, opt=0, extra=''):
		if self.player.gameboard.StartTrace(int(opt)) and reply:
			self.ExtraAction()
			
	def LoseClick(self, opt=0, opt2=''):
		for i in range(int(opt)):
			clicks = self.player.gameboard.rplayer.numclicks
			num = int(opt)
			self.player.gameboard.rplayer.numclicks = max(clicks-num,0)
		
	def TrashProg(self, opt=0, opt2=''):
		for i in range(int(opt)):
			self.player.trashsomething(3)
		
	def damage(self, opt=0, opt2='', opt3=''):
		self.player.gameboard.DoDamage(int(opt),opt2)
		
	def ExtraAction(self):
		pass
	
	def cardaction(self):
		self.printsubroutines()
		actions = { "end": self.EndRun, "trace": self.InitTrace,
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
	
	def RezAction(self):
		print "Don't Rez this card, fool!"
		
	def ScoreAction(self):	
		print "You scored %s!  You gained %d agenda points." %(self.name, self.agendapoints)
		self.player.score += self.agendapoints
		if self.player.score >= 7:
			print "Corp player reaches 7 agenda points and wins"
			sys.exit(0)
		location = self.player.serverlist[self.installedin-1]
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
		print "No Rez Action associated with this card"

class OperationCard(corpcard):
	def __init__(self):
		corpcard.__init__(self)
		self.type = 'Operation'
	
	def InstallAction(self):
		reply = False
		clickcost = 1
		if self.player.checkdo(clickcost, self.rezcost):
			print "You played %s" %self.name
			self.trashaction(True)
			reply = True
		return reply
			

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
			
	def reup(*args):
		print "THE POWER OF PAD CAMPAIGN GIVES YOU:"
			
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
		if self.player.checkdo(3,0):
			print "Gained 7 credits"
			self.player.numcredits += 7

class Hunter(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = 'Hunter'
		self.rezcost = 1
		self.cardtext = 'Subroutine1: Trace3'
		self.icestr = 4
		self.subtype = 'Tracer'
		self.subroutines = {1:['Trace 3',True]}

class Enigma(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Enigma"
		self.subtype = 'Code Gate'
		self.rezcost = 3
		self.icestr = 2
		self.cardtext = 'Subroutine1: Runner loses 1 click.  Subroutine2: End the run'
		self.subroutines = {1:['Lose 1 click',True], 2:['End the run',True]}
			
class WallofStatic(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Wall of Static"
		self.subtype = "Barrier"
		self.rezcost = 3
		self.icestr = 3
		self.cardtext = "Subroutine1: End the run"
		self.subroutines = {1:['End the run',True]}
		
class PriorityRequisition(AgendaCard):
	def __init__(self):
		AgendaCard.__init__(self)
		self.name = "Priority Requisition"
		self.agendapoints = 3
		self.advancetotal = 5
		self.cardtext = "When you score Priority Requisition, you may rez a piece of ice ignoring all costs"
		
	def ScoreAction(self):
		AgendaCard.ScoreAction(self)
		print "You may now rez a piece of ice at no cost"
		escapeclause = 1
		while escapeclause:
			chosencard = self.player.choosefromboard()
			if chosencard:
				if chosencard.type == 'Ice' and not chosencard.faceup:
					chosencard.faceup = True
					print "Rezzed %s" %chosencard.name	
					escapeclause = 0
				else:
					print "Not the card you wanted?"
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
		print "Private Security Force gains the power: 'Pay 1 Click: Do 1 meat damage'."
		self.type = 'Operation' #change type to operation so it can be played
		self.player.playablecardlist.append(self)
		
	def cardaction(self):
		if self.player.gameboard.rplayer.numtags:
			if self.player.checkdo(1,0):
				self.player.gameboard.DoDamage(1, 'meat')
		else:
			print "Runner is not tagged"
			
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
			print "You gained 9 credits"
			
defaultcorpdeck = [PadCampaign, PadCampaign, PadCampaign, MiningCorp, MiningCorp, Hunter, Hunter, Enigma, Enigma, Enigma, WallofStatic, WallofStatic, WallofStatic, PSF, PSF, PSF,PriorityRequisition, PriorityRequisition, PriorityRequisition, HedgeFund, HedgeFund, HedgeFund]

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
		print "You will now draw 3 cards from R&D and install or trash them"
		for i in range(1,4):
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
		self.takeaction=[self.player.takecredit, self.player.takecredit, self.player.takecredit, self.reup]
		for thing in self.takeaction:
			self.player.TurnStartActions.append(thing)
			
	def reup(self, azero):
		self.currentpoints -= 3
		print "THE POWER OF ADONIS CAMPAIGN GAVE YOU 3 CREDITS"
		print "(%d tokens left on Adonis Campaign)" %self.currentpoints
		if not self.currentpoints:
			print "Trashing Adonis Campaign"
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
			print self.readcard()
			print "There are %d tokens on Aggressive Secretary" %self.currentpoints
			print "CORP PLAYER: pay to activate Aggressive Secretary? "
			if gamemods.ask_yes_no("> ") and self.player.checkdo(0,2):
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
			print "You gained 2 clicks"
		
class Shipment(OperationCard):
	def __init__(self):
		OperationCard.__init__(self)
		self.name = "Shipment from Mirrormorph"
		self.rezcost = 1
		self.cardtext = "Immediately install up to 3 cards (spending no clicks but paying all install costs)"
		
	def cardaction(self):
		if OperationCard.InstallAction(self):
			i=3
			while i:
				print self.player.hand
				print "choose a card (%d left): " %i
				print "[type 'Cancel' if you can't play any]"
				x=gamemods.ask_number("card: ", 1, len(self.player.hand.cards)+1)
				if not x: break
				else: 
					try:
						self.player.hand.cards[x-1].InstallAction(0)
						i -= 1
					except:
						print "invalid card"
			
class ArchivedMemories(OperationCard):
	def __init__(self):
		OperationCard.__init__(self)
		self.name = "Archived Memories"
		self.rezcost = 0
		self.cardtext = 'Add 1 card from Archives to HQ'
		
	def cardaction(self):
		print self.player.archivepile
		maxnum = len(self.player.archivepile.cards)+1
		x=gamemods.ask_number("choose card> ", 1, maxnum+1)
		if not x: return False
		if self.InstallAction(): 
			chosencard = self.player.archivepile.cards[x-1]
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
		self.currentpoints=gamemods.ask_number("Choose # of credits: ", 1, self.player.numcredits+1)
		if not self.currentpoints: return False
		if self.player.checkdo(0,self.currentpoints):
			cardlist = []
			server = self.player.serverlist[self.installedin-1]
			for i,ice in enumerate(server.Icelist.cards):
				if ice.faceup: 
					print "("+ str(len(cardlist)+1)+") " + str(ice)
					cardlist.append(server.Icelist.cards[i])
			choice = gamemods.ask_number("Choose Ice to Enhance: ", 1, len(cardlist)+1)
			if not choice: return False
			self.chosencard = cardlist[choice-1]
			self.chosencard.icestr += self.currentpoints
			self.player.TurnStartActions.append(self.reup)
			self.trashaction(True)
	
	def reup(self, azero):
		self.chosencard.icestr -= self.currentpoints
		self.player.TurnStartActions.remove(self.reup)

class ExpData(UpgradeCard):
	def __init__(self):
		UpgradeCard.__init__(self)
		self.name = "Experiental Data"
		self.rezcost = 2
		self.trashcost = 2
		self.cardtext = "All ice protecting this server has +1 strength"

	def RezAction(self):
		for ice in self.player.serverlist[self.installedin-1].Icelist.cards:
			ice.icestr += 1
	
	def trashaction(self, faceup, location=''):
		if self.installedin and self.faceup:
			for ice in self.player.serverlist[self.installedin-1].Icelist.cards:
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
		self.subroutines = {1:['Do 1 brain damage', True], 2:['End the run',True], 3:['End the run', True]}
		self.spendclickoption = True
		
class Ichi(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Ichi 1.0"
		self.rezcost = 5
		self.icestr = 4
		self.subtype = "Sentry"
		self.cardtext = "The Runner can spend 1 click to break any subroutine on Ichi 1.0.  Subroutine1: Trash 1 program.  Subroutine2: Trash 1 program.  Subroutine3: Trace1 - if successful, give the Runner 1 tag and do 1 brain damage."
		self.subroutines = {1:['Trash 1 program',True],2:['Trash 1 program',True], 3:['Trace 1 (extra)',True]}
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
		self.subroutines = {1:['Trash 1 program',True],2:['End the run',True]}
			
class Viktor(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Viktor 1.0"
		self.rezcost = 3
		self.icestr = 3
		self.subtype = "Code Gate"
		self.cardtext = "The Runner can spend 1 click to break any subroutine on Viktor 1.0.  Subroutine1: Do 1 brain damage.  Subroutine2: End the run."
		self.subroutines = {1:['Do 1 brain damage', True], 2: ['End the run',True]}
		self.spendclickoption = True
		
HBdeck = [ABT, ABT, ABT, AdonisCampaign, AdonisCampaign, AdonisCampaign, AggressiveSecretary, AggressiveSecretary, BioticLabor, BioticLabor, BioticLabor, Shipment, Shipment, ArchivedMemories, ArchivedMemories, Troubleshooter, ExpData, ExpData, Heimdall, Heimdall, Ichi, Ichi, Ichi, Rototurret, Rototurret, Viktor, Viktor]


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
		print "Runner has %d tags" %tags
		if not tags: return False
		x=gamemods.ask_number("> ", 0, tags+1)
		if not x: return False
		self.rezcost = x
		if OperationCard.InstallAction(self):
			self.player.advancecard(0,x)
		
class SeaSource(OperationCard):
	def __init__(self):
		OperationCard.__init__(self)
		self.name = "Sea Source"
		self.rezcost = 2
		self.cardtext = "Play only if the Runner made a successful run during his or her last turn.  Trace3 - If successful, give the Runner 1 tag"
	
	def cardaction(self):
		togs = False
		for thing in self.player.gameboard.rplayer.TurnSummary:
			if 'run' in thing: togs = True
		if not togs:
			print "Runner did not make a run last turn"
			return False
		if OperationCard.InstallAction(self):
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
		print "Runner has %d tags" %tags
		if not tags: return False
		if OperationCard.InstallAction(self):
			self.player.gameboard.rplayer.numcredits = 0
			
class AnonymousTip(OperationCard):
	def __init__(self):
		OperationCard.__init__(self)
		self.name = "Anonymous Tip"
		self.rezcost = 0
		self.cardtext = "Draw 3 cards"
	
	def cardaction(self):
		if OperationCard.InstallAction(self):
			self.player.drawcard(0)
			self.player.drawcard(0)
			self.player.drawcard(0)
		
class RedHerrings(UpgradeCard): #not done
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
		for card in self.player.serverlist[self.installedin-1].installed.cards:
			if card.type == 'Agenda':
				card.advancetotal -= 1
	
	def trashaction(self, faceup, location=''):
		if self.installedin and self.faceup:
			for card in self.player.serverlist[self.installedin-1].installed.cards:
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
			print self.readcard()
			print "There are %d tokens on Ghost Branch" %self.currentpoints
			print "Runner receives %d tags" %self.currentpoints
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
		self.player.gameboard.rplayer.numtags -= 2
		
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
		self.subroutines = {1:['Trace 2',True]}
		
	def EncounterAction(self):
		print "Pay 1 credit to advance a card?"
		if gamemods.ask_yes_no("> "):
			self.player.advancecard()
		
class DataRaven(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Data Raven"
		self.rezcost = 4
		self.icestr = 4
		self.subtype = "Sentry - Tracer - Observer"
		self.cardtext = "When the Runner encounters Data Raven, he or she must either take 1 tag or end the run.  Hosted power counter: Give the Runner 1 tag. Subroutine1: Trace3 - If successful, place 1 power counter on Data Raven"
		self.subroutines = {1:['Trace 3 (extra)',True]}
		
	def EncounterAction(self):
		print "Runner must either take 1 tag or end the run"
		if gamemods.ask_yes_no("Take the tag? "):
			self.player.gameboard.rplayer.numtags += 1
		else: self.player.gameboard.winrun = False
		if self.currentpoints: 
			print "Pay tokens off Data Raven to tag runner?"
			ans=gamemods.asknumber("> ", 0, self.currentpoints+1)
			if ans:
				self.player.gameboard.rplayer.numtags += ans
				self.currenpoints -= ans
		
	def ExtraAction():
		print "Place 1 token on Data Raven"
		self.currentpoints += 1
		
class TollBooth(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Tollbooth"
		self.rezcost = 8
		self.icestr = 5
		self.subtype = "Code Gate"
		self.cardtext = "When the Runner encounters Tollbooth, he or she must pay 3 credits, if able.  If the Runner cannot pay 3 credits, end the run.  Subroutine1: End the run."
		self.subroutines = {1:['End the run',True]}
		
	def EncounterAction(self):
		print "Runner must pay 3 credits or end the run"
		if gamemods.ask_yes_no("Pay? ") and self.player.gameboard.rplayer.checkdo(0,3):
			print "Ok, continue"
		else: self.player.gameboard.winrun = False
		
NBNdeck = [Psychographics, Psychographics, SeaSource, SeaSource, ClosedAccounts, ClosedAccounts, AnonymousTip, AnonymousTip, RedHerrings, RedHerrings, SanSan, GhostBranch, GhostBranch, GhostBranch, BreakingNews, BreakingNews, AstroScript, AstroScript, MatrixAnalyzer, MatrixAnalyzer, MatrixAnalyzer, DataRaven, DataRaven, DataRaven, TollBooth, TollBooth, TollBooth]

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
			print "(ok don't pick the same card again)"
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
			print "You haven't scored an agenda this turn"
			return False
		if not self.InstallAction(): return False
		for i,card in enumerate(self.player.deck.cards):
			print "("+str(i+1)+") " + str(card)
		choice = gamemods.ask_number("Choose card: ", 1, len(self.player.deck.cards)+1)
		if not choice: return False
		chosencard = self.player.deck.cards[choice-1]
		self.player.deck.give(chosencard, self.player.hand)
		self.player.deck.shuffle()
		
class ScorchedEarth(OperationCard):
	def __init__(self):
		OperationCard.__init__(self)
		self.name = "Scorched Earth"
		self.rezcost = 3
		self.subtype = "Black Ops"
		self.cardtext = "Play only if the Runner is tagged. Do 4 meat damage"
		
	def cardaction(self):
		if self.player.gameboard.rplayer.numtags > 0:
			if self.InstallAction():
				self.player.gameboard.DoDamage(4, 'meat')
		else:
			print "Runner is not tagged!"
			return False
		
class ResearchStation(UpgradeCard):
	def __init__(self):
		UpgradeCard.__init__(self)
		self.name = "Research Station"
		self.rezcost = 2
		self.trashcost = 3
		self.subtype = "Facility"
		self.cardtext = "Install only in the root of HQ.  Your maximum hand size is +2"
		
	def cardaction(self):
		if self.InstallAction(1,1):
			self.Player.handlimit += 2
		
	def trashaction(self, faceup, location=''):
		if self.installedin and self.faceup: 
			self.Player.handlimit -=2
		corpcard.trashaction(self,faceup,location)
		
class SecuritySub(AssetCard):
	def __init__(self):
		AssetCard.__init__(self)
		self.name = "Security Subcontract"
		self.subtype = "Transaction"
		self.rezcost = 0
		self.trashcost = 3
		self.cardtext = "Pay 1 click and trash a rezzed piece of ice: Gain 4 credits"
		
	def RezAction(self):
		self.type = 'Operation'
		self.player.playablecardlist.append(self)
	
	def cardaction(self):
		if self.player.checkdo(1,0):
			escapeclause = 1
			while escapeclause: 
				print "Choose rezzed ice to trash" 
				chosencard = self.player.choosefromboard()
				if chosencard: 
					if chosencard.type == 'Ice' and chosencard.faceup:
						chosencard.trashaction(True)
						self.player.numcredits += 4
						print "Gained 4 credits"
						escapeclause = 0
					else: 
						print "Invalid card choice"
				else:
					print "cancelling..."
					escapeclause = 0 
					self.player.numclicks += 1
		
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
		self.subroutines = {1:['End the run',True]}

class Shadow(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Shadow"
		self.subtype = "Sentry - Tracer"
		self.rezcost = 3
		self.icestr = 1
		self.cardtext = "Shadow can be advanced and has +1 strength for each advancement token on it. Subroutine1: The Corp gains 2 credits. Subroutine2: Trace 3 - If successful, give the Runner 1 tag"
		self.subroutines = {1:['Corp 2 Credits',True],2:['Trace 3',True]}
		
class Archer(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Archer"
		self.subtype = "Sentry - Destroyer"
		self.rezcost = 4
		self.icestr = 6
		self.cardtext = "As an additional cost to rez Archer, the Corp must forfeit an agenda.  Subroutine1: The Corp gains 2 credits. Subroutine2: Trash 1 program. Subroutine3: Trash 1 program. Subroutine4: End the run." 
		self.subroutines = {1:['Corp 2 Credits',True],2:['Trash 1 program',True],3:['Trash 1 program',True],4:['End the run',True]}
		
class Hadrian(IceCard):
	def __init__(self):
		IceCard.__init__(self)
		self.name = "Hadrian's Wall"
		self.subtype = "Barrier"
		self.rezcost = 10
		self.icestr = 7
		self.advancetotal = 100
		self.cardtext = "Hadrian's Wall can be advanced and has +1 strength for each advancement token on it.  Subroutine1: End the run.  Subroutine2: End the run"
		self.subroutines = {1:['End the run',True],2:['End the run',True]}
		
WCdeck = [Beanstalk, Beanstalk, Beanstalk, ShipmentfromK, ShipmentfromK, AggressiveNegotiation, AggressiveNegotiation, ScorchedEarth, ScorchedEarth, ResearchStation, ResearchStation, SecuritySub, HostileTakeover, HostileTakeover, HostileTakeover, PostedBounty, PostedBounty, IceWall, IceWall, IceWall, Shadow, Shadow, Shadow, Archer, Archer, Hadrian, Hadrian]

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
		self.subroutines = {1:['Do 1 trash',True]}
		
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
		
Jdeck = [NeuralEMP, NeuralEMP, Precognition, Precognition, Akitaro, Snare, Snare, Snare, Zaibatsu, Junebug, Junebug, Junebug, Nisei, Nisei, Nisei, DataMine, DataMine, Chum, Chum, NeuralKatana, NeuralKatana, NeuralKatana, CellPortal, CellPortal, WallofThorns, WallofThorns, WallofThorns]