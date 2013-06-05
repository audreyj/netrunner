import corpcards, runnercards, os

class Hand(object):
	def __init__(self):
		#Keep track of the cards in this hand
		self.cards = []
	
	def __str__(self):
		#Return a string representing the hand
		if self.cards:
			reply = ""
			for i,card in enumerate(self.cards):
				reply += "\n(" + str(i+1) +") " + str(card)
		else: 
			reply = "<empty>"
		return reply 
	
	def clear(self):
		#Reset to an empty hand
		self.cards = []
		
	def add(self, card):
		#Add specified card to this hand
		self.cards.append(card)
		
	def give(self, card, other_hand):
		#Remove the specified card from this hand
		# Add it to a different hand
		self.cards.remove(card)
		other_hand.add(card)
		
class Deck(Hand):
	def populate(self, cardtype):
		print "Populated the deck with:"
		if 'corpdeck' in cardtype:
			for card in corpcards.defaultcorpdeck:
				self.add(card())
			print "Corporation default: "+str(len(corpcards.defaultcorpdeck))	
			if 'HB' in cardtype:
				for card in corpcards.HBdeck:
					self.add(card())
				print "Haas-Biodroid cards: " + str(len(corpcards.HBdeck))
			elif 'NBN' in cardtype: 
				for card in corpcards.NBNdeck:
					self.add(card())
				print "NBN cards: " + str(len(corpcards.NBNdeck))
			elif 'WC' in cardtype: 
				for card in corpcards.WCdeck:
					self.add(card())
				print "Weyland Corporation cards: " + str(len(corpcards.WCdeck))
		elif 'runnerdeck' in cardtype:
			for card in runnercards.defaultrunnerdeck:
				self.add(card())
			print "Runner default: " + str(len(runnercards.defaultrunnerdeck))
			if 'natural' in cardtype.lower():
				for card in runnercards.naturaldeck:
					self.add(card())
				print "Natural cards: " + str(len(runnercards.naturaldeck))
			
	def refdeck(self, cardtype):
		if cardtype == 'corpdeckHB':
			newlist = list(set(corpcards.defaultcorpdeck + corpcards.HBdeck))	
		elif cardtype == 'corpdeckWC':
			newlist = list(set(corpcards.defaultcorpdeck + corpcards.WCdeck))
		elif cardtype == 'corpdeckNBN':
			newlist = list(set(corpcards.defaultcorpdeck + corpcards.NBNdeck))
		if cardtype == 'runnerdecknatural':
			newlist = list(set(runnercards.shortdeck + runnercards.naturaldeck))
		for card in newlist:
				self.add(card())
				
	def shuffle(self):
		import random
		random.shuffle(self.cards)
		print "Shuffled the deck"
	
	def deal(self, hands, per_hand=5):
		for rounds in range(per_hand):
			for hand in hands:
				if self.cards:
					top_card = self.cards[0]
					self.give(top_card, hand)
				else:
					print "Out of cards!"
					
	def mulligan(self, hand):
		while len(hand.cards):
			hand.give(hand.cards[len(hand.cards)-1], self)
		self.shuffle()
		self.deal([hand], 5)

class Server(object):
	def __init__(self):
		self.Icelist = Hand()
		self.installed = Hand()
		self.name = '<Empty Server>'
		self.MoreRoomForCards = True
	
	def __str__(self):
		return self.name
	
	def describeserver(self, showall=True):
		reply = "| %-15s |" %self.name
		if self.installed.cards:
			reply += "\n   => Installed Cards  => "
			for i, card in enumerate(self.installed.cards):
				if card.faceup or showall:
					reply += "\n\t (" +str(i+1)+") " +str(card)
					if card.faceup == False:
						reply += " [===FACE DOWN===] " 
				else:
					reply += "\n\t (" +str(i+1)+") ===A Facedown installed card==="
				if card.currentpoints:
						reply += " [===%d Token(s)===] " %card.currentpoints
		else:
			reply += "\n   => <No Installed Cards> "
		if self.Icelist.cards:
			reply += "\n   => Installed Ice  =>"
			for i,card in enumerate(self.Icelist.cards):
				if card.faceup or showall:
					reply += "\n\t (" +str(i+1)+") " +str(card)
					if card.faceup == False:
						reply += " [===FACE DOWN===] " 
				else:
					reply += "\n\t (" +str(i+1)+") ===A Facedown installed card==="
				if card.currentpoints:
						reply += " [===%d Token(s)===] " %card.currentpoints
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
		self.score=0
		self.numcredits=5
		self.handlimit=5
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
		if self.numclicks<clickcost:
			print "Not Enough Clicks for this action!"
		elif self.numcredits<creditcost:
			print "Not Enough Credits for this action!"
		else:
			if clickcost or creditcost: 
				print "You paid %d click(s) and %d credit(s)." %(clickcost, creditcost)
			self.numclicks -= clickcost
			self.numcredits -= creditcost
			reply = True
		return reply
	
	def showopts(self,opt=''):
		if opt == 'status':
			self.mystatus()
			print "| Number of Clicks = %d" %self.numclicks
			print "| Number of Credits = %d" %self.numcredits
			print "| Hand limit = %d" %self.handlimit
			print "| Current # of cards = %d" %len(self.hand.cards)
			print "| Agenda Points Scored = %d" %self.score
		elif opt in ['enemy','opponent']:
			self.gameboard.ShowOpponent(self.type)
		elif opt in ['hand','cards']:
			print "------- Player's Hand --------"
			print self.hand
		elif opt.isdigit():
			try:
				self.hand.cards[int(opt)-1].readcard()
			except:
				print "Invalid card number"
		elif opt == 'board':
			self.showmyboard()
		elif opt == 'archives':
			print self.archivepile
		elif opt == 'all':
			for i,card in enumerate(self.referencedeck.cards):
				print "("+str(i+1)+") " + str(card)
			choice = ask_number("Choose card: ", 1, len(self.referencedeck.cards)+1)
			if choice:
				self.referencedeck.cards[choice-1].readcard()
		else:
			print "Valid SHOW objects: HAND, STATUS, ARCHIVES, BOARD"
	
	def drawcard(self, clickcost=1):
		if clickcost not in range(0,4): clickcost = 1
		print 'Draw 1 card from R&D'
		if self.checkdo(clickcost, 0):
			self.deck.deal([self.hand],1)
			self.turnsummary.append('Drew a card')
			
	def takecredit(self, clickcost=1):
		print 'Gain 1 credit from bank'
		if clickcost not in range(0,4): clickcost = 1
		if self.checkdo(clickcost, 0):
			self.numcredits += 1
			self.turnsummary.append('Took a credit from the bank')
			print "Number of Credits: " +str(self.numcredits)

	def playcard(self, cardnum=0, clickcost=1):
		if cardnum == 0:
			print "Cards on the board that you can play: " 
			for i,card in enumerate(self.playablecardlist):
				print "("+str(i+1)+") " + str(card)
			choice = ask_number("Choose card to Play: ", 1, len(self.playablecardlist)+1)
			if not choice: return 0
			chosencard = self.playablecardlist[choice-1]
		elif int(cardnum) in range(1, len(self.hand.cards)+1):		
			chosencard = self.hand.cards[int(cardnum)-1]
			if chosencard.type not in ['Operation', 'Event']:
				print "Did you mean to INSTALL this card?  It can't be PLAYED"
				return 0
		else:
			print "Not the right card?"
			return False
		if 'cardaction' in dir(chosencard):
			print "Play " + chosencard.name
			self.turnsummary.append('Played ' +str(chosencard))
			chosencard.cardaction()
			if chosencard.subtype == 'Transaction' and self.identity=='WC':
				print "WC Power: Gain 1 credit"
				self.takecredit(0)
	
	def installcard(self, cardnum=0): #install something
		try:
			chosencard = self.hand.cards[int(cardnum)-1]
		except:
			print "Non-valid card choice"
			return 0
		if chosencard.type in ['Operation', 'Event']:
			print "Did you mean to PLAY this card?"
		else:
			print "Installing " + str(chosencard)
			chosencard.InstallAction()
	
	def trashmine(self, opt=''):
		chosencard = self.choosefromboard(True)
		if chosencard:
			question = "Really trash " +str(chosencard.name) +"??" 
			if ask_yes_no(question):
				if not chosencard.installedin:
					chosencard.faceup = False
				chosencard.trashaction(chosencard.faceup)
				self.turnsummary.append('Trashed a card')
	
	def firstturn(self, deckname, id):
		self.deck.populate(deckname+id)
		self.identity=id
		for i,card in enumerate(self.deck.cards):
			card.player = self
			card.id = i
		self.referencedeck.refdeck(deckname+id)
		self.deck.shuffle()
		self.deck.deal([self.hand], self.handlimit)
		tempmull = 3
		while tempmull:
			print self.hand
			if ask_yes_no("Mulligan? (%d Mulligans remain) => "%tempmull):
				self.deck.mulligan(self.hand)
				tempmull -= 1
			else: 
				tempmull = 0
	
	def TurnStart(self):	
		self.firstcall = True
		self.turnsummary = []
		#print self.TurnStartActions
		for dothing in self.TurnStartActions:
			dothing(0)
	
	def TurnEnd(self):
		while len(self.hand.cards)>self.handlimit:
			print "You have too many cards in your hand."
			self.showopts('hand')
			ans = 0
			while not ans:
				ans = ask_number("Discard which card? ", 1, len(self.hand.cards)+1)
			self.hand.cards[ans-1].trashaction()
		for dothing in self.TurnEndActions:
			dothing()
		os.system('cls')
		print "-------- Opponent Turn Summary ---------"
		for thing in self.turnsummary:
			print "  - " + thing
	
	
class CorpPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		self.type = 'corp'
		self.serverlist = [hqserver(), rdserver(), archives()]		
	
	def showmyboard(self):
		for server in self.serverlist:
				print server.describeserver()
	
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
		for i,card in enumerate(cardlist): 
			if card.installedin:
				location = self.serverlist[card.installedin-1].name
			else: location = "your hand"
			print "("+ str(i+1)+") "+str(card)+" --> in "+location
		choice = ask_number("Choose card: ", 1, len(cardlist)+1)
		if not choice: return 0
		chosencard = cardlist[choice-1]
		return chosencard
	
	def mystatus(self):
		print "--------- Corporation Player ----------"
		print "| Identity = Haas-Biodroid"
		print "| ID Power = The first time you install a card each turn, gain 1 credit" 
		print "| Remaining Cards in HQ = %d" %len(self.deck.cards)
		print "| Number of Cards in Archives = %d" %len(self.archivepile.cards)
		
	def advancecard(self, clickcost=1, amt=1): #advance a card
		chosencard = self.choosefromboard()
		if not chosencard: return 0
		elif not chosencard.advancetotal: 
			print "Not an advanceable card"
			return 0
		if self.checkdo(clickcost, 1):
			chosencard.currentpoints += amt
			self.turnsummary.append('Advanced a card')
			print "Advanced %s" %chosencard.name
			if chosencard.advancetotal <= chosencard.currentpoints:
				chosencard.ScoreAction()
		
	def purgevirus(self, opt): #purge virus counters
		print 'purge virus counters'
		self.turnsummary.append('purged virus counters')
		clickcost = 3
		creditcost = 0
	
	def trashsomething(self, opt=''): #trash a card from somewhere
		if not opt:
			print "One of your cards, or one of your opponent's?"
			print "\t (1) One of mine \n\t (2) One of the runner's"
			opt = ask_number("> ", 1, 3)
			if not choice: return False
		if opt == 1:
			self.trashmine()
		elif opt == 2:
			print 'Trash 1 resource if runner is tagged'
			if self.gameboard.rplayer.numtags:
				chosencard=1
				while chosencard:
					chosencard = self.gameboard.rplayer.choosefromboard()
					if chosencard and chosencard.type == 'Resource':
						if self.checkdo(1,2):
							chosencard.trashaction()
							self.turnsummary.append('Trashed %s' %chosencard)
							chosencard = 0
					else:
						print "Not a resource card?"
			else: 
				print "Runner is not tagged!"
		elif opt == 3: 
			print "Trash one of the runner's programs"
			chosencard=1
			while chosencard:
				chosencard = self.gameboard.rplayer.choosefromboard()
				if chosencard and chosencard.type == "Program":
					print "Trashing " +str(chosencard)
					chosencard.trashaction()
					chosencard = 0
		else: print "Whaaaaaaaaat"

	def rezcard(self, opt=''): #rez a card that's on the board already
		chosencard = self.choosefromboard()
		if not chosencard: return 0
		elif chosencard.faceup or chosencard.rezcost == '<None>':
			print "This card does not need rezzing"
			return 0
		elif self.checkdo(0, chosencard.rezcost):
			chosencard.faceup = True
			chosencard.RezAction()
			self.turnsummary.append('Rezzed ' +str(chosencard))
			print "Rezzed %s" %chosencard.name
			
	def RunActions(self, servernum, icecounter):
		actions = { "show": self.showopts, "play": self.playcard,
					"rez": self.rezcard}
		chosenserver = self.serverlist[servernum-1]
		while 1:
			print "---------------------------"
			print "Runner is making a run on: " + str(chosenserver)
			print "Approaching Ice #" + str(icecounter+1)
			print "Take an action? (Type 'end' when done)"
			userinput = raw_input('> ').lower()
			wordlist = userinput.split()
			if wordlist[0] == 'end': return 0
			elif wordlist[0] in actions:
				do = actions[wordlist[0]]
				do(*wordlist[1:])
			else:
				print "action not in list: "
				print actions.keys()
				
	def playturn(self):
		actions = { "show": self.showopts, "advance":self.advancecard,
					"install": self.installcard, "draw": self.drawcard,
					"take": self.takecredit, "purge": self.purgevirus,
					"trash": self.trashsomething, "play": self.playcard,
					"rez": self.rezcard}
		print "---------- Start Corporation Turn -------------"
		self.numclicks = 3
		self.TurnStart()	
		self.drawcard(0)
		while 1:
			print "-----------------------------------------------"
			print "It is Corp turn.  You have %d clicks remaining." %self.numclicks
			if not self.numclicks:
				print "(Type 'end' to end your turn)"
			userinput = raw_input('> ').lower()
			wordlist = userinput.split()
			if not self.numclicks and wordlist[0] =='end': break
			elif wordlist[0] in actions:
				do = actions[wordlist[0]]
				#try:
				do(*wordlist[1:])
				#except: 
				#	print "Not understanding your nouns" 
			else:
				print "action not in list: "
				print actions.keys()
		self.TurnEnd()
				
class RunnerPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		self.type = 'runner'
		self.programlimit = 4
		self.memoryused = 0
		self.boardhand = Hand()
		self.numtags = 0
		self.numlinks = 1
		self.usedcardslist = []
		self.preventset = {}
		
	def mystatus(self):
		print "---------------- Runner Player ---------------"
		print "| Identity: Kate McCaffrey (Natural)"
		print "| ID Power: First install cost on hardware or program -1"
		print "| Program Memory Limit: %d" %self.programlimit
		print "| Current Memory Usage: %d" %self.memoryused
		print "| Current Number of Tags: %d" %self.numtags
		print "| Current Link Strength: %d" %self.numlinks
		
	def showmyboard(self):	
		print "-------------- Runner's Rig -------------"
		for card in self.boardhand.cards:
			print "\n\t-> "+str(card),
			if card.currentpoints:
				print "  [=== %d Token(s) ===]" %card.currentpoints,
		print "\n"		
	
	def choosefromboard(self, showhand=False):
		cardlist = []
		i=0
		for card in self.boardhand.cards:
			cardlist.append(card)
			print "("+ str(i+1)+") "+str(card)
			i += 1
		if showhand:
			for card in self.hand.cards:
				cardlist.append(card)
				print "("+ str(i+1)+") "+str(card)+" (in your hand)"
				i += 1
		choice = ask_number("Choose card: ", 1, len(cardlist)+1)
		if not choice: return 0
		chosencard = cardlist[choice-1]
		return chosencard 
	
	def removetags(self, opt=''):
		if self.numtags and self.checkdo(1,2):
			self.numtags -= 1
			print "Removed one tag"
			self.turnsummary.append('Removed a tag')
	
	def PreventCheck(self, var):
		reply = False
		cardlist = [x for x in self.preventset.keys() if self.preventset[x]==var]
		while cardlist:
			for i,card in enumerate(cardlist):
				print "\t (0) - Do nothing"
				print "\t ("+str(i+1)+") - Play " + str(card)
			ans = ask_number("> ", 0, len(cardlist)+1)
			if not ans:
				break
			elif cardlist[ans-1].cardaction():
				reply = True
				break
		return reply
	
	def breaksubroutines(self, ice):
		self.usedcardslist = []
		while 1: 
			print "You've encountered ice - time to get to breaking"
			ice.printsubroutines()
			print "Use commands 'show', 'play', or 'spend'"
			print "(Type 'end' when done)"
			choosebreak=False
			userinput = raw_input('> ').lower()
			wordlist = userinput.split()
			if wordlist[0] == 'end': return 0
			elif wordlist[0] == 'show':
				if wordlist[1] == 'ice':
					ice.readcard()
				else:
					self.showopts(*wordlist[1:])
			elif ice.spendclickoption and wordlist[0] == 'spend':
				if self.checkdo(1,0):
					choosebreak=True
			elif wordlist[0] == 'play':
				chosencard = self.choosefromboard()
				if 'breakaction' in dir(chosencard) and chosencard.breakaction(ice):
					self.usedcardslist.append(chosencard)
					choosebreak=True
			else:
				print "Invalid option for breaking, try again"
			if choosebreak:
				ice.printsubroutines()
				s=ask_number("Break which subroutine: ", 1, len(ice.subroutines)+1)
				if s:
					ice.subroutines[s][1]=False
	
	def exposecard(self):
		self.gameboard.ShowOpponent('runner')
		
	def standardrun(self, clickcost=1):
		if self.checkdo(clickcost,0):
			self.gameboard.ShowOpponent('runner')
			print '---------------------------'
			for i, server in enumerate(self.gameboard.cplayer.serverlist):
				print "\t ("+str(i+1)+") "+str(server)
			servernum = ask_number("Choose server to run on: ", 1, i+2)
			if not servernum: return False
			self.turnsummary.append('Made a run')
			if self.gameboard.StartRun(servernum):
				self.gameboard.AccessCards(servernum)
			else:
				print "Run Failed!"
			for card in self.usedcardslist:
				card.Reset()
	
	def playturn(self):
		actions = { "show": self.showopts, "run": self.standardrun,
					"install": self.installcard, "draw": self.drawcard,
					"take": self.takecredit, "remove": self.removetags,
					"trash": self.trashmine, "play": self.playcard}
		print "---------- Start Runner Turn -------------"
		self.numclicks = 4
		self.TurnStart()	
		while 1:
			print "-----------------------------------------------"
			print "It is Runner turn.  You have %d clicks remaining." %self.numclicks
			if not self.numclicks:
				print "(Type 'end' to end your turn)"
			userinput = raw_input('> ').lower()
			wordlist = userinput.split()
			if not self.numclicks and wordlist[0]=='end': break
			elif wordlist[0] in actions:
				do = actions[wordlist[0]]
				#try:
				do(*wordlist[1:])
				#except: 
				#	print "Not understanding your nouns" 
			else:
				print "action not in list: "
				print actions.keys()
		self.TurnEnd()
		
def ask_yes_no(question):
	response = None
	while response not in ("y","n","yes","no"):
		response = raw_input(question).lower()
	if response in ('y','yes'): return True
	elif response in ('n','no'): return False

def ask_number(question, low, high):
	response = None
	while response not in range(low, high):
		rawresponse = raw_input(question)
		if rawresponse == 'cancel':
			response = 0
			break
		try: response = int(rawresponse)
		except: pass
	return response 
	
