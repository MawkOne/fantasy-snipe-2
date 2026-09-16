// Mock data for the UHHP UFA Auction (live draft). Replace with Railway API calls later.

const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export interface AuctionTeam {
  id: string;
  name: string;
  emoji: string;
  capRoom: number; // $ available
  maxBid: number;
  nominating?: boolean;
}

export interface Bid {
  id: string;
  amount: number;
  teamEmoji: string;
  teamName: string;
  time: string;
}

export interface NominationSlot {
  order: number;
  teamEmoji: string;
  teamName: string;
}

export const AUCTION_META = {
  title: "UFA Auction Round 2",
  subtitle: "Nomination Order (Round Robin)",
  onClock: "3 / 12",
  nominatingTeam: "Puck Pirates",
  nominatingEmoji: "🏴‍☠️",
  ownersOnline: "12/12 owners",
};

export const AUCTION_PLAYER = {
  id: "marner",
  name: "Mitch Marner",
  position: "RW",
  team: "TOR",
  age: 27,
  contract: "1.0 x $11.0M (UFA)",
  tag: "Elite",
  headshotUrl: headshot(8478483),
  marketValue: 29,
  note: "UFA · No trade clause expected",
  maxTerm: 7,
};

export const AUCTION_STATE = {
  highBid: 28,
  highBidTeam: "Harbour Ice",
  minRaise: 1,
  secondsStart: 18,
};

/** 12 teams in the auction, cap room + max bid. */
export const AUCTION_TEAMS: AuctionTeam[] = [
  { id: "harbour-ice", name: "Harbour Ice", emoji: "🐻‍❄️", capRoom: 47, maxBid: 200 },
  { id: "puck-pirates", name: "Puck Pirates", emoji: "🏴‍☠️", capRoom: 62, maxBid: 200, nominating: true },
  { id: "slapshot-city", name: "Slapshot City", emoji: "🐙", capRoom: 18, maxBid: 200 },
  { id: "benders-burgers", name: "Bender's Burgers", emoji: "🍔", capRoom: 71, maxBid: 200 },
  { id: "victoria-whalers", name: "Victoria Whalers", emoji: "🐋", capRoom: 12, maxBid: 200 },
  { id: "snipe-show", name: "Snipe Show", emoji: "🤡", capRoom: 95, maxBid: 200 },
  { id: "ice-cold-takes", name: "Ice Cold Takes", emoji: "🥅", capRoom: 33, maxBid: 200 },
  { id: "mighty-drunks", name: "Mighty Drunks", emoji: "🍺", capRoom: 27, maxBid: 200 },
  { id: "zamboners", name: "The Zamboners", emoji: "🧊", capRoom: 8, maxBid: 200 },
  { id: "net-results", name: "Net Results", emoji: "🥅", capRoom: 51, maxBid: 200 },
  { id: "pylons", name: "Pylons", emoji: "🚧", capRoom: 39, maxBid: 200 },
  { id: "offside-wieners", name: "Offside Wieners", emoji: "🌭", capRoom: 66, maxBid: 200 },
];

export const RECENT_BIDS: Bid[] = [
  { id: "b1", amount: 28, teamEmoji: "🐻‍❄️", teamName: "Harbour Ice", time: "9:41:12 AM" },
  { id: "b2", amount: 27, teamEmoji: "🥅", teamName: "Ice Cold Takes", time: "9:41:05 AM" },
  { id: "b3", amount: 26, teamEmoji: "🐻‍❄️", teamName: "Harbour Ice", time: "9:40:58 AM" },
  { id: "b4", amount: 24, teamEmoji: "🤡", teamName: "Snipe Show", time: "9:40:41 AM" },
  { id: "b5", amount: 22, teamEmoji: "🏴‍☠️", teamName: "Puck Pirates", time: "9:40:12 AM" },
  { id: "b6", amount: 20, teamEmoji: "🍔", teamName: "Bender's Burgers", time: "9:39:47 AM" },
  { id: "b7", amount: 18, teamEmoji: "🐙", teamName: "Slapshot City", time: "9:39:20 AM" },
  { id: "b8", amount: 15, teamEmoji: "🌭", teamName: "Offside Wieners", time: "9:38:54 AM" },
  { id: "b9", amount: 12, teamEmoji: "🐻‍❄️", teamName: "Harbour Ice", time: "9:38:02 AM" },
  { id: "b10", amount: 10, teamEmoji: "🏴‍☠️", teamName: "Puck Pirates", time: "9:37:30 AM" },
];

export const NOMINATION_QUEUE: NominationSlot[] = [
  { order: 4, teamEmoji: "🍔", teamName: "Bender's Burgers" },
  { order: 5, teamEmoji: "🐋", teamName: "Victoria Whalers" },
  { order: 6, teamEmoji: "🤡", teamName: "Snipe Show" },
  { order: 7, teamEmoji: "🥅", teamName: "Ice Cold Takes" },
  { order: 8, teamEmoji: "🍺", teamName: "Mighty Drunks" },
];

export const NOMINATION_NOTE = "Round 2 continues after this nomination";
