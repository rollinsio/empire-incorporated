"""Invented name parts for generated people. Combined at random, never copied from real people."""

FIRST_NAMES = (
    "Aldo Alira Amsel Anneka Arden Arlo Asha Aven Bale Barrin Bryn Caddoc Calla Callum Carys Casimir "
    "Cassia Cedric Ciran Corra Dace Dalric Danna Darek Davin Delia Desik Dorne Edda Edric Elara Elian "
    "Emrys Enna Esme Evran Faren Fenna Ferris Finnick Garrow Gavren Gessa Halden Hale Hessa Ilka Imra "
    "Isolde Ivor Jarek Jaska Jessa Joren Kael Kalla Kaspar Kesia Kier Kirra Lannic Larsa Leda Lorne "
    "Lysander Maelis Maren Marik Merrin Mesa Nadia Nalen Nerys Nils Noa Odile Oren Orla Osric "
    "Pela Perrin Petra Quell Quinn Rafe Rain Rell Remy Rhosa Riven Rosk Rowan Saela Sarik Senna Seren "
    "Silas Sola Soren Talia Tamsin Tarn Teague Tessa Theron Tilda Torin Treva Tyce Ulla Ursel Vala "
    "Vance Vela Venn Vesna Vira Wren Wyatt Xan Yara Yorik Zane Zara Zeva Brisk Cato Daro Elsk Fallon "
    "Garnet Hollis Ines Jory Kestin Linnea Maddox Neve Orrin Pax Rhett Sabel Tova Ulric Wilde"
).split()

LAST_NAMES = (
    "Abernathe Adrel Alcorne Ambrose Ancel Ardent Arkwell Ashby Aster Avrane Bailin Barrowe Bastide "
    "Belcourt Blackwood Bracken Brannic Bresk Calder Calloway Carrow Castellan Chalke Corrin Craddock "
    "Crane Crestwell Dallan Darrow Daventry Delane Desmont Dravis Drummond Dunmore Easton Ellery Elsmore "
    "Embry Errant Falkner Farrow Fenwick Fiore Galloway Garron Gaunt Graylin Greaves Halloran Harrick "
    "Hawthorne Hesk Holloway Hune Illing Ingram Iverson Jarrow Kade Kaine Keller Kendrick Kessel Kirwan "
    "Lancer Larkin Leith Lorne Lowell Lusk Maddox Marlow Marrek Mathers Merrick Mordant Morrow Nash "
    "Nevins Norcott Oakes Orlen Osgood Palin Parrish Pell Penrose Pike Quarrel Radlow Ramsey Ravell "
    "Redgrave Renner Rhydon Rorke Rothe Rusk Sable Salter Sarne Sorrel Stagg Starke Stroud Tallis "
    "Tarrant Teague Thorne Tibbet Torvald Tregar Tull Ulmer Vance Varrick Venner Vexley Voren "
    "Wade Wakefield Warrick Welles Whitlock Winter Wolcott Wren Yarrow Yorke Zander Zell Ashcombe "
    "Brightwater Coldbrook Dunleavy Everhart Fairholm Glenmore Hartwell Ironside Kingsley Longmire"
).split()

GERMAN_FIRST_NAMES = (
    "Anja Bernd Clemens Dagmar Detlef Elke Frieda Gerold Gisela Hannes Heike Henrik Ilse Jannik Jutta "
    "Karsten Katrin Lothar Lutz Margit Matthias Nele Ortwin Petra Rainer Renate Sigrun Silke Thilo Uwe "
    "Volker Wiebke Wolfram Annegret Bastian Dörte Falko Götz Ingrid Jürgen"
).split()

GERMAN_LAST_NAMES = (
    "Albrecht Baumann Brückner Dietrich Eckhardt Falkenberg Fischer Graf Hahn Hartmann Heinrich Jäger "
    "Kessler Köhler Krämer Lange Lorenz Maurer Neumann Pfeiffer Reinhardt Ritter Schäfer Schmitt "
    "Schröder Seidel Sommer Stein Vogt Wagner Weber Weiß Winkler Wolff Zimmermann Brenner Engel Huber"
).split()

SPECIES = (
    ("Human", 930),
    ("Near-Human", 35),
    ("Duros", 10),
    ("Sullustan", 10),
    ("Pau'an", 8),
    ("Chagrian", 7),
)

HOMEWORLDS = (
    ("Coruscant", 160), ("Corellia", 70), ("Eriadu", 40), ("Carida", 60), ("Kuat", 55), ("Corulag", 45),
    ("Chandrila", 35), ("Lothal", 40), ("Alsakan", 30), ("Brentaal", 30), ("Anaxes", 30), ("Raxus", 25),
    ("Naboo", 20), ("Alderaan", 20), ("Fondor", 30), ("Sluis Van", 20), ("Scarif", 15), ("Mon Gazza", 10),
    ("Bespin", 10), ("Ord Mantell", 15), ("Tepasi", 10), ("Garel", 15), ("Abregado-rae", 10),
)

GERMAN_HOMEWORLDS = (("Eriadu", 70), ("Fondor", 15), ("Kuat", 15))

STREETS = (
    "Orbital Way", "Meridian Row", "Lantern Street", "Harbour Lane", "Skyline Terrace", "Foundry Road", "Beacon Walk",
    "Gantry Street", "Comet Close", "Nebula Court", "Senate Mile", "Tidewater Lane", "Arcology Drive", "Spire Avenue",
)
DISTRICTS = ("Upper Level 12", "Upper Level 31", "Mid Level 140", "Mid Level 212", "Old Quarter", "Harbour District", "North Ring", "South Ring")
RELATIONS = ("spouse", "partner", "parent", "sibling", "adult child", "friend")

ASCII_FOLD = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "'": "", " ": ""})


def email_local_part(first: str, last: str) -> str:
    return f"{first}.{last}".translate(ASCII_FOLD).lower()
