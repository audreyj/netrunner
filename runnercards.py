import gamemods

class runnercard(object):
	def __init__(self):
		self.name = '<None>'
		self.rezcost='<None>'
		self.type= '<None>'
		self.icestr = '<None>'
		self.subtype='<No Subtype>'
		self.cardtext='<None>'
		self.currentpoints = 0
		self.takeaction = []
		self.player = ''
		self.id = '<None>'
		self.programcost = 0
		self.installedin = 0
		
	def __str__(self):
		reply = self.name + " (" + self.type +": " + self.subtype + ")"
		return reply
	
	def readcard(self):
		print "----- Card Name = %s -------" %self.name
		print "| Card Type = %s:%s" %(self.type,self.subtype)
		if self.type == 'Program':
			print "| Ice Strength = " + str(self.icestr)
			print "| Memory Unit Cost = " + str(self.programcost)
		print "| Install Cost = " + str(self.rezcost)
		print "| Card Text = " + self.cardtext
		print "------------------------------\n"
			
	def InstallAction(self, clickcost=1):
		reply = False
		discount = 0
		if self.player.firstcall and self.type in ['Program', 'Hardware']:
			print "Natural Power: -1 cost of install"
			discount = 1
		if self.player.memoryused+self.programcost>self.player.programlimit:
			print "Memory Limit Exceeded, cannot install this card!"
			return reply
		if self.player.checkdo(clickcost, max(self.rezcost-discount,0)):
			self.currentpoints = 0
			self.player.hand.give(self, self.player.boardhand)
			self.player.memoryused += self.programcost
			self.installedin = 1
			self.RezAction()
			self.player.turnsummary.append('Installed ' +str(self))
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
		print "Trashed " + str(self)
		
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
			print "Ice not %s type" %type
			return False
		else:
			return True
	
	def IBincreasestr(self, ice, factor=1):
		if ice.icestr>self.icestr:
			print "Pay %d credits to increase strength to equal ice?" %(ice.icestr-self.icestr)*factor
			if gamemods.ask_yes_no("> ") and self.player.checkdo(0,(ice.icestr-self.icestr)*factor):
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
		if self.player.checkdo(1,0):
			self.player.numcredits += 2
			self.currentpoints -= 2
			print "You gained 2 credits"
			print "(%d credits left on Armitage Codebusting)" %self.currentpoints
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
		print "You gained 1 Link"
		
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
		if self.player.checkdo(1,self.rezcost):
			self.player.numcredits += 9
			print "You gained 9 credits"
			self.trashaction()
		
class Infiltration(EventCard):
	def __init__(self):
		EventCard.__init__(self)
		self.name = "Infiltration"
		self.rezcost = 0
		self.cardtext = "Gain 2 credits or expose 1 card"
		
	def cardaction(self):
		if self.player.checkdo(1,self.rezcost):
			print "Your choices: \n\t (1) Gain 2 credits \n\t (2) Expose 1 card"
			choice = gamemods.ask_number("You choose: ", 1, 3)
			if choice == 1:
				self.player.numcredits += 2
				print "Gained 2 credits"
			elif choice == 2:
				print "expose 1 card (todo)"
			else:
				print "that's not a choice...."
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
		if self.player.checkdo(1,0):
			self.currentpoints += 1
			
	def breakaction(self, ice):
		self.IBincreasestr(ice)
		if ice.icestr <= self.icestr:
			s=1
			while s:
				print "Pay 1 credit to break 1 subroutine"
				ice.printsubroutines()
				s=gamemods.ask_number("Break which subroutines (0 for done): ",0,len(ice.subroutines)+1)
				if s and ice.subroutines[s][1] and self.player.checkdo(0,1):
					ice.subroutines[s][1]=False
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
		print "Program Limit +2, Link +2"
		self.player.programlimit += 2
		self.player.numlinks += 2
		self.currentpoints = 2
		self.player.TurnStartActions.append(*self.takeaction)
		
	def breakaction(self, someice):
		if self.currentpoints:
			print "Take 2 credits for ice breaking"
			self.savenum = self.player.numcredits
			self.player.numcredits += 2
			self.currentpoints -= 2
		else:
			print "No credits on Toolbox to use!" 
		
	def Reset(self, azero):
		print "Putting 2 credits back on Toolbox"
		self.currentpoints = 2
		if self.player.numcredits >= self.savenum:
			print "You have more credits now than when you started this run..."
			self.player.numcredits = self.savenum

class Akamatsu(HardwareCard):
	def __init__(self):
		HardwareCard.__init__(self)
		self.name = "Akamatsu Mem Chip"
		self.rezcost = 1
		self.cardtext = "+1 Program Limit"
		self.subtype = "Chip"
		
	def RezAction(self):
		print "Program Limit +1"
		self.player.programlimit += 1
		
	def trashaction(self):
		if self.installedin:
			self.player.programlimit -= 1
			print "Program Limit -1"
		runnercard.trashaction(self)
		
class PersonalTouch(HardwareCard):
	def __init__(self):
		HardwareCard.__init__(self)
		self.name = "The Personal Touch"
		self.subtype = "Mod"
		self.rezcost = 2
		self.cardtext = "Install The Personal Touch only on an icebreaker.  Hosted icebreaker has +1 strength"
		
	def RezAction(self):
		gk=1
		while gk:
			chosencard = self.player.choosefromboard()
			if chosencard and 'Icebreaker' in chosencard.subtype:
				chosencard.icestr += 1
				self.installedin = chosencard
				gk=0
			elif not chosencard: 
				return False
			else:
				print "fail!"
		self.player.TurnStartActions.append(self.reup)
			
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
		print "Link Strength +1"
		self.player.numlinks += 1
		indeck = False
		for card in self.player.deck.cards:
			if card.name == "Rabbit Hole":
				print "Found another copy of Rabbit Hole in the stack."
				if gamemods.ask_yes_no("Install? ") and self.player.checkdo(0,2):
						self.player.deck.give(card, self.player.boardhand)
						self.player.numlinks += 1
				indeck = True
		if not indeck: 
			print "Can't find Rabbit Hole in stack"
	
	def trashaction(self):
		if self.installedin:
			self.player.numlinks -= 1
			print "Number of Links -1"
		runnercard.trashaction(self)

class Diesel(EventCard):
	def __init__(self):
		EventCard.__init__(self)
		self.name = "Diesel"
		self.rezcost = 0
		self.cardtext = "Draw 3 cards"
		
	def cardaction(self):
		if self.player.checkdo(1,self.rezcost):
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
		self.player.preventset[self]='trash'
		
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
		if self.player.checkdo(0,self.rezcost):
			print self.cardtext
			self.player.showopts("hand")
			choice = gamemods.ask_number("Install: ", 1, len(self.player.hand.cards)+1)
			while not choice: 
				chosencard = self.player.hand.cards[choice-1]
				if chosencard.type in ['Program', 'Hardware']:
					chosencard.rezcost = max(chosencard.rezcost-3,0)
					if chosencard.InstallAction():
						self.trashaction()
					return True
				else:
					print "Card is not program or hardware"

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
		if self.player.numclicks==4:
			chosencard = self.player.choosefromboard()
			if chosencard:
				chosencard.trashaction()
				self.player.numcredits += 3
		else:
			print "Cannot play this now"
	
class Tinkering(EventCard):
	def __init__(self):
		EventCard.__init__(self)
		self.name = "Tinkering"
		self.subtype = "Mod"
		self.rezcost = 0
		self.cardtext = "Choose a piece of ice.  That ice gains sentry, code gate, and barrier until the end of the turn" 
		
	def cardaction(self):
		if self.player.checkdo(1,self.rezcost):
			self.player.gameboard.ShowOpponent('runner')
			cardlist = []
			for server in self.player.gameboard.cplayer.serverlist:
				for ice in server.Icelist.cards:
					cardlist.append(ice)
			for i,card in enumerate(cardlist):
				location = self.player.gameboard.cplayer.serverlist[card.installedin-1].name
				if card.faceup:
					print "("+str(i+1)+") " +str(card) +" ---> in "+location
				else:
					print "("+str(i+1)+") --A facedown Ice-- ---> in"+location
			choice = gamemods.ask_number("Choosecard: ", 1, len(cardlist)+1)
			if not choice: return False
			chosencard = cardlist[choice-1]
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
			self.player.gameboard.AccessCards(2,3)
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
		if self.player.checkdo(1,0):
			self.player.numcredits += 2
			print "You gained 2 credits"
			
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
			print "Pay 1 credit to break 1 Code Gate subroutine"
			if self.player.checkdo(0,1):
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
		self.takeaction=[self.reup]
		
	def RezAction(self):
		self.player.preventset[self]='netdamage'
		
	def cardaction(self):
		if not self.currentpoints and self.player.checkdo(0,1):
			print "Prevented 1 net damage"
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
			print "Pay 2 credits to break 2 Barrier subroutines"
			if self.player.checkdo(0,2):
				s=1
				n=2
				while s and n:
					ice.printsubroutines()
					s=gamemods.ask_number("Break which subroutines (0 for done): ",0,len(ice.subroutines)+1)
					if s and ice.subroutines[s][1]:
						ice.subroutines[s][1]=False
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
		if not self.IBtypecheck('Sentry',ice): return False
		self.IBincreasestr(ice, 2)
		if self.icestr >= ice.icestr:
			print "Pay 1 credit to break 1 Sentry subroutine"
			if self.player.checkdo(0,1):
				return True
		
	def Reset(self):
		self.icestr = 1
	
naturaldeck = [Toolbox, Akamatsu, Akamatsu, PersonalTouch, PersonalTouch, RabbitHole, RabbitHole, Diesel, Diesel, Diesel, Sacrificial, Sacrificial, Modded, Modded, Aesops, Tinkering, Tinkering, Tinkering, MakersEye, MakersEye, MakersEye, MagnumOpus, MagnumOpus, GordianBlade, GordianBlade, GordianBlade, NetShield, NetShield, BatteringRam, BatteringRam, PipeLine, PipeLine]

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
			for i,card in enumerate(self.player.ScoredCards):
				print " ("+str(i+1)+") " + str(card)
			print "Forfeit an agenda?"
			choice = gamemods.ask_number("> ", 1, len(self.player.ScoredCards)+1)
			if not choice: return False
			if self.player.checkdo(1,0):
				chosencard = self.player.ScoredCards[choice-1]
				print "Forfeited " +str(chosencard) +", gained 9 credits"
				self.player.ScoredCards.remove(chosencard)
				self.player.numcredits += 9
		else: 
			print "No Agendas to forfeit!"
		
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
		
cyborgdeck = [DataDealer, BankJob, BankJob, AccountSiphon, AccountSiphon, SpecialOrder, SpecialOrder, SpecialOrder, InsideJob, InsideJob, InsideJob, EasyMark, EasyMark, EasyMark, ForgedOrders, ForgedOrders, ForgedOrders, Lemuria, Lemuria, Desperado, Decoy, Decoy, CrashSpace, CrashSpace, Ninja, Ninja, Sneakdoor, Sneakdoor, Aurora, Aurora, FemmeFatale, FemmeFatale]

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
		
noisedeck = [Grimoire, Cyberfeeder, Cyberfeeder, Cyberfeeder, IceCarver, Wyldside, Wyldside, DejaVu, DejaVu, DemolitionRun, DemolitionRun, DemolitionRun, Stimhack, Stimhack, Stimhack, Datasucker, Datasucker, Wyrm, Wyrm, Parasite, Parasite, Parasite, Corroder, Corroder, Djinn, Djinn, Medium, Medium, Mimic, Mimic, Yog, Yog]