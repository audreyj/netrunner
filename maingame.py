import gamemods, os, sys

class gameboard(object):
	def __init__(self):
		self.cplayer = gamemods.CorpPlayer()
		self.cplayer.gameboard = self
		self.rplayer = gamemods.RunnerPlayer()
		self.rplayer.gameboard = self
		self.continuerun = True
		
	def ShowOpponent(self, callertype):
		if callertype == 'runner':
			self.cplayer.showopts("status")
			for server in self.cplayer.serverlist:
				print server.describeserver(False)
		else:
			self.rplayer.showopts("status")
			self.rplayer.showmyboard()
		
	def StartRun(self, servernum, bypass=False):
		chosenserver = self.cplayer.serverlist[servernum-1]
		icecounter = len(chosenserver.Icelist.cards)
		self.winrun=True
		while self.winrun and icecounter:
			print "Approaching outermost Ice card..."
			icecounter -= 1
			icecard=chosenserver.Icelist.cards[icecounter]
			os.system('cls')
			self.cplayer.RunActions(servernum, icecounter)
			if icecard.faceup and not bypass:
				icecard.readcard()
				icecard.EncounterAction()
				self.rplayer.breaksubroutines(icecard)
				icecard.cardaction()
				icecard.ResetIce()
			if icecounter and gamemods.ask_yes_no("Jack out? "):
				self.winrun = False
				icecounter = 0
		return self.winrun
		
	def AccessCall(self, chosencard, location, skiptrash = True):
		print chosencard
		if chosencard.type == 'Agenda':
			print "You've stolen %s! You gained %d agenda points." %(chosencard.name, chosencard.agendapoints)
			self.rplayer.score += chosencard.agendapoints
			if self.rplayer.score >= 7: 
				print "Runner player reaches 7 agenda points and wins"
				sys.exit(0)
			location.give(chosencard, self.rplayer.ScoredCards)
			if chosencard.installedin:
				self.cplayer.serverlist[chosencard.installedin-1].MoreRoomForCards = True
			chosencard.advancetotal = 0
			chosencard.type = "Agenda: Scored"
			chosencard.player = self.rplayer
			self.rplayer.turnsummary.append('Scored ' +str(chosencard))
			return True
		if skiptrash and 'RunnerAccessed' in dir(chosencard):
			chosencard.RunnerAccessed()
		if skiptrash and chosencard.trashcost != '<None>':
			print "Pay %d Credits to trash this card?" %chosencard.trashcost
			if gamemods.ask_yes_no("> ") and self.rplayer.checkdo(0,chosencard.trashcost):
				chosencard.trashaction(True, location)
		else:
			print "Nothing to be done with this card, returning it..."
		
	def AccessCards(self, servernum, numcards=1):
		chosenserver = self.cplayer.serverlist[servernum-1]
		print "Run Successful, Accessed " +str(chosenserver)
		print "Accessing Installed Cards..." 
		cardlist = chosenserver.installed.cards
		numaccessible = len(cardlist)
		while numaccessible:
			reply = ''
			for i,card in enumerate(cardlist):
				reply += "\n\t ("+str(i+1)+") " 
				if card.faceup:
					reply += str(card)
				else:
					reply += "==== A FACEDOWN CARD ===="
				if card.currentpoints:
					reply += " [==== %d token(s)====]" %card.currentpoints
			print reply
			num = gamemods.ask_number("Choose card: ", 1, len(cardlist)+1)
			if num:
				self.AccessCall(cardlist[num-1], chosenserver.installed)
			numaccessible -= 1
		print "No installed cards to access"
		if servernum == 1: #HQ server
			handlen = len(self.cplayer.hand.cards)
			print "Pick a card from 1 to " + str(handlen)
			ans = gamemods.ask_number("> ", 1, handlen+1)
			if ans:
				self.AccessCall(self.cplayer.hand.cards[ans-1], self.cplayer.hand)
		elif servernum == 2: #R&D server
			for i in range(numcards):
				print "Accessing a card from R&D..."
				self.AccessCall(self.cplayer.deck.cards[i], self.cplayer.deck)
		elif servernum == 3: #Archives
			print "Accessing Archives..."
			for card in self.cplayer.archivepile.cards:
				self.AccessCall(card, self.cplayer.archivepile, False)
				
	def StartTrace(self, basetrace):
		print "Corporation initiates trace"
		print "Add credits to enhance trace? (%d base)" %basetrace
		print "Your current credits: " + str(self.cplayer.numcredits)
		addt=gamemods.ask_number("Credits to add: ",0,self.cplayer.numcredits+1)
		atk = basetrace +addt
		print "Corporation trace strength: %d" %atk
		links = self.rplayer.numlinks
		print "Runner Link strength: %d" %links
		if links >= atk:
			print "Runner avoids trace"
			return False
		else:
			print "Your current credits: " + str(self.rplayer.numcredits)
			question = "Pay %d credits to avoid trace? " %(atk-links)
			if gamemods.ask_yes_no(question) and self.rplayer.checkdo(0,atk-links):
				print "Runner pays to avoid trace"
				return False
			else:
				self.rplayer.numtags += 1
				print "Runner receives 1 tag"
				return True
		
	def DoDamage(self, amt, type):
		if type=='brain':
			print "Runner player takes %d brain damage" %amt
			if self.rplayer.handlimit < amt:
				print "RUNNER SUSTAINS FATAL DAMAGE ==> RUNNER LOSES"
				sys.exit(0)
			self.rplayer.handlimit -= amt
		else:
			if type == 'net' and self.rplayer.PreventCheck('netdamage'): amt-=1
			print "Runner player takes %d net/meat damage" %amt
			if len(self.rplayer.hand.cards)<amt:
				print "RUNNER SUSTAINS FATAL DAMAGE ==> RUNNER LOSES"
				sys.exit(0)
			for dmg in range(amt):
				self.rplayer.showopts('hand')
				ans = 0
				while not ans:
					ans = gamemods.ask_number("Discard which card? ", 1, len(self.rplayer.hand.cards)+1)
				self.rplayer.hand.cards[ans-1].trashaction(False)
		
	def ExposeCard(self):
		pass
		
	def playgame(self):
		os.system('cls')
		self.cplayer.firstturn('corpdeck','NBN')
		os.system('cls')
		self.rplayer.firstturn('runnerdeck','natural')
		os.system('cls')
		while self.cplayer.score<7 and self.rplayer.score<7:
			self.cplayer.playturn()
			self.rplayer.playturn()
			

newgame = gameboard()
newgame.playgame()