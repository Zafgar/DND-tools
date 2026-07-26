"""Legendat — Cunaen historian kaksi absoluuttista huippuvoimaa.

**Keisari Tarquvas Redfei** (CR 28) ja **Matriarkka Cazna Icharyd**
(CR 26) ovat kampanjan tärkeimmät hahmot: heidän konfliktinsa muokkasi
nykyisen maailman ja aloitti Time of Guidance -ajanlaskun. Molemmat ovat
kosmisia poikkeavuuksia, joiden voima ylittää tavallisen CR 20 -katon,
joten heille on rakennettu **myyttiset statblockit** (mythic trait =
toinen vaihe, joka laukeaa kun ensimmäinen "kuolema" tapahtuu).

Pelinjohtajan raakapohja on täydennetty kokonaiseksi kahdesta suunnasta:

*Tarquvas* — lähtökohtana CR 28, HP 750, AC 25, STR/CON 30, Verun
regeneraatio 50/vuoro, Faerzress-tatuoinnit ja Unstoppable Will. Tähän on
lisätty hänen kuvattu varustuksensa ja taistelutapansa: **musta
obsidiaaninen kahden käden miekka "Aki'kor"**, **vaalea
titaaniluu-täyshaarniska**, ja **kehoon liitettyjen Faerzress-kristallien
magia** (innate spellcasting, joka on force-, salama- ja
todellisuudenvääntömagiaa — ei kirjaloitsijan arsenaalia). Lisäksi
lorepohjaiset kyvyt: 25-vuotiaana hän kaatoi kymmeniä miehiä ja taisteli
yksin lohikäärmettä vastaan, hän murtautui drowien maagisen suodattimen
läpi, ja hänen 3/5 Veru-palastaan tekevät hänestä kentällä
tappamattoman — juuri siksi Cazna joutui vangitsemaan hänen SIELUNSA
eikä voinut yksinkertaisesti surmata häntä.

*Cazna* — lähtökohtana CR 26, HP 350, AC 22, INT 28, sielukone,
Archmage Supreme, Tarquvasin kruunu, Sielujen purkaus ja mythic trait.
Tähän on lisätty pelinjohtajan huomio siitä, että **matriarkka käyttää
myös miekkaa taitavasti**: 3 500 vuoden harjoittelu tekee hänestä
terälaulun (bladesong) mestarin, joka lyö sielumiekallaan ja loitsii
samalla vuorolla. Lisäksi hänen puolustuskerroksensa on mallinnettu
kokonaan: Mage Armor → Shield → Terälaulu → sielukoneen
vahingonsiirto → Legendary Resistance → mythic-vaihe.

Molemmilla on lair-toiminnot omassa paikassaan (Tarquvas Veru-paikalla,
Cazna Kristallijärven palatsissa) sekä ``tactics``-kentässä konkreettinen
kierrosjärjestys, jolla pelinjohtaja saa heidät toimimaan oikein.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature, Item


monsters = [
    # ================================================================= #
    # KEISARI TARQUVAS REDFEI — CR 28 (myyttinen)
    # Titaaninen muoto: aika ennen vangitsemista.
    # ================================================================= #
    CreatureStats(
        name="Keisari Tarquvas Redfei", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Lawful Evil",
        armor_class=25,
        armor_type="Vaalea titaaniluu-täyshaarniska + Garruthan iho "
                   "(Natural Armor)",
        hit_points=750, hit_dice="52d8+520", speed=40, climb_speed=40,
        abilities=AbilityScores(strength=30, dexterity=18, constitution=30,
                                intelligence=16, wisdom=20, charisma=24),
        saving_throws={"Strength": 18, "Dexterity": 12, "Constitution": 18,
                       "Intelligence": 11, "Wisdom": 13, "Charisma": 15},
        skills={"Athletics": 18, "Intimidation": 15, "Perception": 13,
                "Survival": 13, "Insight": 13, "History": 11},
        senses="Darkvision 120 ft., Truesight 30 ft. (Faerzress), "
               "Passive Perception 23",
        languages="Common, Orc, Goblin, Undercommon, Abyssal, "
                  "Deep Speech (Faerzressin kautta)",
        damage_resistances=["force", "lightning", "necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        damage_immunities=["poison", "psychic"],
        condition_immunities=["Charmed", "Frightened", "Poisoned",
                              "Exhaustion", "Paralyzed", "Stunned", "Prone",
                              "Grappled", "Restrained"],
        # Faerzress-kristallit ihossa: magia on synnynnäistä, ei opiskeltua.
        spellcasting_ability="Charisma", spell_save_dc=23,
        spell_attack_bonus=15,
        spell_slots={"3rd": 3, "4th": 3, "5th": 3, "6th": 2, "7th": 1},
        spell_names=[
            "Faerie Fire", "Darkness", "Lightning Bolt", "Dispel Magic",
            "Fear", "Blight", "Wall of Force", "Telekinesis",
            "Chain Lightning", "Disintegrate", "Plane Shift",
        ],
        cantrip_names=["Eldritch Blast", "Booming Blade", "Lightning Lure"],
        actions=[
            Action("Multiattack",
                   "Neljä iskua: Aki'kor tai Titaaninen isku vapaasti "
                   "sekoitettuna. Yksi niistä voidaan korvata "
                   "Kristallimagialla.",
                   0, "", 0, "", is_multiattack=True, multiattack_count=4,
                   multiattack_targets=["Aki'kor", "Aki'kor", "Aki'kor",
                                        "Aki'kor"]),
            Action("Aki'kor",
                   "Melee, kahden käden obsidiaanimiekka (reach 10 ft). "
                   "Täysin musta obsidiaaniterä, joka jättää haavan johon "
                   "Faerzress vuotaa: kohde ei voi saada healingia ennen "
                   "vuoronsa loppua.",
                   19, "4d6+3d10", 10, "slashing", range=10, reach=10,
                   properties=["heavy", "two-handed", "reach"]),
            Action("Titaaninen isku",
                   "Melee paljain käsin. Maa vavahtaa: DC 26 STR tai kohde "
                   "kaatuu (Prone) ja työntyy 15 ft taaksepäin.",
                   19, "4d12", 10, "force", range=10, reach=10,
                   applies_condition="Prone", condition_save="Strength",
                   condition_dc=26),
            Action("Garruthan raivo",
                   "Recharge 5-6. Titaanin huuto Tarquvasin suusta: 90 ft "
                   "kartio, DC 26 CON tai 15d10 force (puolet "
                   "onnistuneella). Kaikki voimakentät ja maagiset esteet "
                   "(Wall of Force, Forcecage, Globe of Invulnerability, "
                   "Otiluke's Resilient Sphere) alueella TUHOUTUVAT ilman "
                   "pelastusheittoa, ja maasto muuttuu vaikeaksi maastoksi.",
                   0, "15d10", 0, "force", range=90, aoe_radius=90,
                   aoe_shape="cone", condition_save="Constitution",
                   condition_dc=26),
            Action("Kristallimagia",
                   "Tarquvas polttaa yhden ihoonsa upotetun "
                   "Faerzress-kristallin ja loitsii yhden loitsun "
                   "(DC 23, +15 osumaan). Tämä ei vaadi keskittymistä "
                   "toisin kuin tavallinen magia — kristalli pitää "
                   "loitsun kasassa hänen puolestaan.",
                   0, "", 0, "", range=120),
            Action("Veru-repäisy",
                   "1/taistelu. Tarquvas repii selkäänsä sidotusta "
                   "Veru-palasesta kaistaleen ja iskee sillä: 60 ft linja, "
                   "DC 26 CON tai 10d12 necrotic ja kohteen max HP laskee "
                   "saman verran taistelun loppuun. Tarquvas ottaa itse "
                   "50 vahinkoa (ohittaa regeneraation tämän vuoron).",
                   0, "10d12", 0, "necrotic", range=60, aoe_radius=60,
                   aoe_shape="line", condition_save="Constitution",
                   condition_dc=26),
        ],
        bonus_actions=[
            Action("Titaanin harppaus",
                   "Hyppää 60 ft ilman vauhtia. Laskeutuminen: kaikki 15 ft "
                   "säteellä tekevät DC 26 STR -pelastuksen tai ottavat "
                   "4d10 force ja kaatuvat.",
                   0, "4d10", 0, "force", range=60, aoe_radius=15,
                   aoe_shape="sphere", action_type="bonus",
                   applies_condition="Prone", condition_save="Strength",
                   condition_dc=26),
            Action("Keisarin käsky",
                   "Yksi Tarquvasin liittolainen 60 ft sisällä käyttää "
                   "reaktionsa tehdäkseen yhden aseiskun.",
                   0, "", 0, "", range=60, action_type="bonus"),
        ],
        reactions=[
            Action("Obsidiaanitorjunta",
                   "Kun häntä vastaan osutaan melee-iskulla, hän saa +8 AC "
                   "sitä iskua vastaan. Jos isku menee silti ohi, hyökkääjä "
                   "ottaa 3d10 force -vahinkoa terän sirpaleista.",
                   0, "3d10", 0, "force", range=10, action_type="reaction"),
        ],
        features=[
            Feature("Legendary Resistance",
                    "5/päivä: kun Tarquvas epäonnistuu pelastusheitossa, "
                    "hän voi valita onnistuvansa sen sijaan.",
                    feature_type="passive", uses_per_day=5),
            Feature("Verun regeneraatio",
                    "Tarquvas palauttaa 50 HP jokaisen vuoronsa alussa. "
                    "Mikään yksittäinen vahinkotyyppi ei sammuta tätä — ei "
                    "tuli, ei radiant, ei Chill Touch. Vain Veru-palasten "
                    "irrottaminen tai sielun vangitseminen pysäyttää sen. "
                    "Tämän takia häntä silvottiin taistelukentillä "
                    "toistuvasti eikä hän kuollut.",
                    mechanic="regeneration", mechanic_value="50"),
            Feature("Faerzress-tatuoinnit",
                    "Faerzress-kristalli on jauhettu hänen vereensä ja "
                    "tatuoitu ihoonsa. Hänellä on ETU kaikkiin taikuutta "
                    "vastaan tehtäviin pelastusheittoihin, ja tason 5 tai "
                    "sitä matalammat loitsut EIVÄT VAIKUTA häneen "
                    "lainkaan — ei vahinkoa, ei ehtoja, ei pelastusheittoa.",
                    mechanic="magic_resistance"),
            Feature("Kolme viidestä Veru-palasesta",
                    "Tarquvaksen selkään on sidottu 3/5 Veru-ihon "
                    "palasista. Hän on kirjaimellisesti maailmantitaani "
                    "Garruthan ruumiin jatke: häntä ei voi tappaa "
                    "pysyvästi taistelukentällä. 0 HP:ssä hän vain "
                    "sammuu hetkeksi (ks. Unstoppable Will). Ainoa tapa "
                    "poistaa hänet pelistä on VANGITA HÄNEN SIELUNSA "
                    "(Imprisonment tai vastaava artefakti) — juuri niin "
                    "Cazna teki.",
                    feature_type="passive"),
            Feature("Unstoppable Will (Mythic Trait)",
                    "Kun Tarquvasin HP putoaisi nollaan ensimmäisen kerran, "
                    "hänen Oknar-toteeminsa ottaa vallan sen sijaan: hän "
                    "palauttaa 400 HP, nousee heti pystyyn, saa yhden "
                    "ylimääräisen vuoron välittömästi, ja loppu taistelun "
                    "ajan jokainen hänen iskunsa tekee lisäksi 3d10 force "
                    "ja 3d10 lightning -vahinkoa. Tämä on toinen vaihe — "
                    "kohtaaminen kannattaa laskea kahtena taisteluna "
                    "(mythic encounter, 2× XP).",
                    feature_type="passive", uses_per_day=1),
            Feature("Oknarin herääminen",
                    "Vaihesiirtymä: kun HP putoaa 25 %:iin, toteemin ääni "
                    "alkaa kuulua — Tarquvas menettää Obsidiaanitorjuntansa "
                    "mutta saa etua kaikkiin osumaheittoihin ja tekee "
                    "Multiattackilla viisi iskua neljän sijasta.",
                    feature_type="passive", phase_trigger_hp_pct=0.25,
                    phase_description="Oknar-toteemi herää: +1 isku, etu "
                                      "osumaheittoihin, ei enää torjuntaa."),
            Feature("Titaanin voima",
                    "Tarquvas lasketaan Huge-kokoiseksi kaikissa "
                    "kantamisen, raahaamisen, työntämisen ja grapple-"
                    "kilpailujen tarkistuksissa, ja hänellä on etu "
                    "STR-kilpailuheittoihin. Hän kaatoi 25-vuotiaana "
                    "kymmeniä aseistettuja miehiä yksin.",
                    feature_type="passive"),
            Feature("Siege Monster",
                    "Kaksinkertainen vahinko rakenteille ja esineille. "
                    "Aki'kor halkaisee kivimuurin yhdellä vuorolla.",
                    feature_type="passive"),
            Feature("Lohikäärmentappaja",
                    "Tarquvas taisteli yksin lohikäärmettä vastaan ja "
                    "voitti. Hän on immuuni lohikäärmeen Frightful "
                    "Presencelle ja saa etua pelastusheittoihin "
                    "henkäysaseita vastaan; puolittuneesta vahingosta "
                    "hän ottaa vain neljänneksen.",
                    feature_type="passive"),
            Feature("Suodattimen murtaja",
                    "Hän murtautui nuorena drowien maagisen suodattimen "
                    "läpi Aterterraan. Mikään maaginen este, portti tai "
                    "sulkeva rituaali ei estä häntä: hän voi käyttää "
                    "toimintonsa murtaakseen minkä tahansa maagisen "
                    "esteen tai tasoportin (automaattinen onnistuminen "
                    "9. tasoa vastaan).",
                    feature_type="passive"),
            Feature("Kristallimagia (Innate Spellcasting)",
                    "CHA, DC 23, +15 osumaan. Ihoon upotetut "
                    "Faerzress-kristallit loitsivat hänen puolestaan: "
                    "loitsut eivät vaadi häneltä keskittymistä eikä "
                    "komponentteja, eikä Counterspell voi peruuttaa niitä "
                    "alle 6. tason slotilla. Ei kirjaloitsijan arsenaali — "
                    "pelkkää force-, salama- ja "
                    "todellisuudenvääntömagiaa.",
                    feature_type="passive"),
            Feature("Reaktio: Obsidiaanitorjunta",
                    "Ks. reaktiot. Poistuu käytöstä Oknarin heräämisen "
                    "jälkeen.", feature_type="reaction"),
            Feature("Garruthan raivo", "Recharge 5-6.", recharge="5-6"),
            Feature("Legendaarinen: Isku",
                    "Legendaarinen toiminto (1): yksi Aki'kor-isku.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Titaanin askel",
                    "Legendaarinen toiminto (1): liikkuu koko nopeutensa "
                    "provosoimatta. Reitille jäävä maasto halkeaa "
                    "vaikeaksi maastoksi.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Kristallisalama",
                    "Legendaarinen toiminto (2): 60 ft linja, DC 23 DEX tai "
                    "6d8 lightning (puolet onnistuneella). Osuma katkaisee "
                    "kohteen keskittymisen ilman pelastusheittoa.",
                    feature_type="legendary", legendary_cost=2,
                    damage_dice="6d8", damage_type="lightning", save_dc=23,
                    save_ability="Dexterity"),
            Feature("Legendaarinen: Garruthan kuiskaus",
                    "Legendaarinen toiminto (2): yksi olento 120 ft sisällä "
                    "kuulee kahlitun titaanin huudon. DC 23 WIS tai 4d10 "
                    "psychic ja Frightened vuoronsa loppuun; "
                    "epäonnistuneella heitolla kohde näkee myös totuuden "
                    "Garruthasta (pelinjohtaja saa paljastaa lore-palan).",
                    feature_type="legendary", legendary_cost=2,
                    damage_dice="4d10", damage_type="psychic", save_dc=23,
                    save_ability="Wisdom", applies_condition="Frightened"),
            Feature("Lair: Veru-paikan pulssi",
                    "Lair-toiminto (init 20): Veru-laitteen lähellä maasta "
                    "purskahtaa Faerzress. Kaikki Tarquvasin viholliset "
                    "60 ft sisällä tekevät DC 23 CON -pelastuksen tai "
                    "ottavat 4d10 force ja menettävät bonustoimintonsa "
                    "seuraavalla vuorollaan.",
                    feature_type="lair"),
            Feature("Lair: Keisarin lippu",
                    "Lair-toiminto (init 20): Aki'korkezin lippu nousee. "
                    "Kaikki Tarquvasin liittolaiset saavat 30 temp HP ja "
                    "immuniteetin Frightenediin kierroksen loppuun.",
                    feature_type="lair"),
            Feature("Lair: Titaanin sydämenlyönti",
                    "Lair-toiminto (init 20): maa lyö kuin sydän. Kaikki "
                    "muut olennot 90 ft sisällä tekevät DC 23 STR "
                    "-pelastuksen tai kaatuvat; Tarquvas palauttaa 50 HP.",
                    feature_type="lair"),
        ],
        legendary_action_count=3, legendary_resistance_count=5,
        items=[
            Item("Aki'kor — musta obsidiaanimiekka", item_type="weapon",
                 slot="main_hand", equipped=True, rarity="artifact",
                 requires_attunement=True, attuned=True,
                 damage_dice="4d6+3d10",
                 description="Valtava kahden käden miekka, täysin musta "
                             "obsidiaanin väristä terästä, nimetty "
                             "Aki'korkez-imperiumin mukaan. Terä ei "
                             "heijasta valoa lainkaan. Haavaan vuotaa "
                             "Faerzress: kohde ei voi saada healingia "
                             "vuoronsa loppuun. Halkaisee kiven ja "
                             "voimakentät."),
            Item("Vaalea titaaniluu-täyshaarniska", item_type="armor",
                 slot="armor", equipped=True, rarity="artifact",
                 armor_category="heavy", base_ac=21, ac_bonus=4,
                 max_dex_bonus=0,
                 description="Kaunis, lähes valkoinen täyshaarniska, valettu "
                             "Garruthan luusta ja kiillotettu peilikirkkaaksi "
                             "— tarkoituksellinen vastakohta mustalle "
                             "terälle. Ei anna stealth-haittaa, koska "
                             "haarniska liikkuu kantajansa lihaksena."),
            Item("Kolme Veru-ihon palasta", item_type="wondrous",
                 equipped=True, rarity="artifact",
                 description="Sidottu selkään elävällä lihalla. 3/5 "
                             "palasista. Antaa regeneraation ja tekee "
                             "kantajastaan titaanin ruumiin jatkeen. "
                             "Viidennen palasen sitominen olisi vapauttanut "
                             "Garruthan — Dimerius petti hänet juuri "
                             "kolmannen sitomisen aikana."),
            Item("Oknar-toteemi", item_type="wondrous", equipped=True,
                 rarity="legendary",
                 description="Örkkiheimon esi-isien toteemi hänen "
                             "kaulassaan. Kun keho pettää, toteemi ottaa "
                             "vallan (Unstoppable Will)."),
        ],
        lore="\"Unohdettu Keisari\". Syntyi sorrettuun örkkien ja "
             "puoliörkkien Aki'korkez-imperiumiin ja oli poikkeusyksilö jo "
             "nuorena: 25-vuotiaana hän kaatoi kymmeniä miehiä yksin ja "
             "taisteli lohikäärmettä vastaan. Murtautui drowien maagisen "
             "suodattimen läpi Aterterraan, altistui Faerzressille ja näki "
             "totuuden kahlitusta maailmantitaani Garruthasta. Keräsi 3/5 "
             "Veru-ihon palasista, jauhoi Faerzress-kristallia vereensä ja "
             "tatuoi sen ihoonsa — muuttui titaanin voiman jatkeeksi. "
             "Tavoite: purkaa vanha maailma, vapauttaa titaani ja alistaa "
             "kaikki muut rodut. Hänen sielunsa on YHÄ vangittuna "
             "Matriarkka Caznan kruunun vihreään timanttiin astraalimerellä, "
             "missä haavat eivät koskaan sulkeudu mutta kuolema ei tule.",
        tactics="Kierros 1: Titaanin harppaus keskelle ryhmää, Multiattack "
                "Aki'korilla, legendaariset Kristallisalamalla loitsijoihin "
                "(katkaisee keskittymisen ilman savea). Kierros 2: "
                "Garruthan raivo heti kun ryhmä nostaa Wall of Forcen tai "
                "kokoontuu — kartio tuhoaa voimakentät automaattisesti. "
                "Muista että alle 6. tason loitsut eivät vaikuta häneen "
                "LAINKAAN: älä pyydä pelastusheittoja niistä, kerro vain "
                "että ne hajoavat tatuointeihin. Kun HP < 25 %, Oknar "
                "herää: 5 iskua ja etu, ei enää torjuntaa. Kun HP putoaa "
                "0:aan, ÄLÄ lopeta taistelua — Unstoppable Will nostaa "
                "hänet 400 HP:llä ja hän saa heti ylimääräisen vuoron. "
                "Ainoa oikea voittotapa on sielun vangitseminen tai "
                "Veru-palasten irrottaminen (DC 26 STR/Arcana, toiminto, "
                "provosoi).",
        loot_table="Aki'kor (artefakti, kahden käden miekka), vaalea "
                   "titaaniluu-täyshaarniska (artefakti), 3 Veru-ihon "
                   "palasta (kampanjan tärkein artefakti — nämä Krusk "
                   "kantaa nykyään), Oknar-toteemi, Aki'korkezin "
                   "keisarisinetti.",
        habitat="Aki'korkez / Aterterra / Veru-paikat",
        challenge_rating=28.0, xp=120000, proficiency_bonus=8),

    # ================================================================= #
    # MATRIARKKA CAZNA ICHARYD — CR 26 (myyttinen)
    # Nykyhetki: 3 500+ vuotta vanha arkkimaagi ja miekkamestari.
    # ================================================================= #
    CreatureStats(
        name="Cazna Icharyd", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil",
        armor_class=22,
        armor_type="Mage Armor + DEX + sielukilpi (Shield 27, "
                   "Terälaulu 31)",
        hit_points=350, hit_dice="41d8+164", speed=30, fly_speed=30,
        abilities=AbilityScores(strength=10, dexterity=22, constitution=18,
                                intelligence=28, wisdom=24, charisma=24),
        saving_throws={"Dexterity": 14, "Constitution": 12,
                       "Intelligence": 17, "Wisdom": 15, "Charisma": 15},
        skills={"Arcana": 25, "History": 25, "Insight": 15,
                "Perception": 15, "Deception": 15, "Intimidation": 15,
                "Acrobatics": 14},
        senses="Darkvision 120 ft., Truesight 60 ft., "
               "Passive Perception 25",
        languages="Elvish, Undercommon, Deep Speech, Abyssal, Common, "
                  "Primordial (osaa 3 500 vuoden aikana kaiken)",
        damage_resistances=["force", "necrotic", "cold", "psychic"],
        condition_immunities=["Charmed", "Frightened", "Exhaustion",
                              "Poisoned"],
        spellcasting_ability="Intelligence", spell_save_dc=25,
        spell_attack_bonus=17,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 2, "7th": 2, "8th": 2, "9th": 2},
        spell_names=[
            # Kestosuojat ja vastatoimet — hän ei ota iskuja vastaan
            "Shield", "Mage Armor", "Silvery Barbs", "Mirror Image",
            "Counterspell", "Dispel Magic", "Misty Step", "Silence",
            # Hallinta — hän vääntää säännöt
            "Slow", "Fear", "Banishment", "Otiluke's Resilient Sphere",
            "Greater Invisibility", "Polymorph", "Hold Monster",
            "Telekinesis", "Wall of Force", "Dominate Person",
            "Synaptic Static", "Forcecage", "Dominate Monster",
            "Power Word Stun", "Feeblemind",
            # Tuho — Faerzress-kylmänä versiona
            "Cone of Cold", "Chain Lightning", "Disintegrate", "Harm",
            "Finger of Death", "Sunburst", "Plane Shift",
            # Loppupeli
            "Meteor Swarm", "Time Stop", "Power Word Kill",
            "Imprisonment", "Foresight",
        ],
        cantrip_names=["Toll the Dead", "Mind Sliver", "Ray of Frost",
                       "Fire Bolt", "Mage Hand"],
        actions=[
            Action("Multiattack",
                   "Kaksi Sielumiekka-iskua — TAI yksi loitsu ja yksi "
                   "Sielumiekka-isku (ks. Archmage Supreme).",
                   0, "", 0, "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Icharydin sielumiekka",
                                        "Icharydin sielumiekka"]),
            Action("Icharydin sielumiekka",
                   "Melee, finesse-terä joka on juonut 3 500 vuoden ajan. "
                   "Osumalla Cazna saa 10 temp HP ja kohde menettää "
                   "1d6 max HP taistelun loppuun.",
                   17, "2d8+3d10", 5, "necrotic", range=5,
                   properties=["finesse", "light"]),
            Action("Sielujen purkaus",
                   "Recharge 5-6. Cazna laukaisee Kristallijärven "
                   "energian: 60 ft säde, DC 25 CON tai 10d10 necrotic "
                   "(puolet onnistuneella). Drow-magia repii sielun irti "
                   "— tämä vahinko OHITTAA sekä necrotic-resistanssin "
                   "ETTÄ necrotic-immuniteetin. Jokainen olento joka "
                   "kuolee tähän, imeytyy sielukoneeseen (Cazna palauttaa "
                   "yhden käytetyn loitsupaikan, max 7. taso).",
                   0, "10d10", 0, "necrotic", range=60, aoe_radius=60,
                   aoe_shape="sphere", condition_save="Constitution",
                   condition_dc=25),
            Action("Tarquvasin kruunu: muisto",
                   "Cazna pakottaa yhden olennon 60 ft sisällä näkemään "
                   "Tarquvasin muiston mantereen räjäyttämisestä. DC 25 WIS "
                   "tai 8d10 psychic ja Stunned vuoronsa loppuun; "
                   "onnistuneella puolet eikä Stunned. Kohde tietää tämän "
                   "jälkeen totuuden Garruthasta.",
                   0, "8d10", 0, "psychic", range=60,
                   applies_condition="Stunned", condition_save="Wisdom",
                   condition_dc=25),
            Action("Loitsiminen",
                   "INT, DC 25, +17 osumaan. Täysi 9. tason loitsija "
                   "(Wizard 20 / Bladesinger). Kaksi 9. tason "
                   "loitsupaikkaa.",
                   0, "", 0, "", range=150),
        ],
        bonus_actions=[
            Action("Terälaulu (Bladesong)",
                   "3 500 vuoden miekkaharjoittelu. Bonustoiminto: +9 AC "
                   "(INT), etu Acrobaticsiin, +1d8 force jokaiseen "
                   "sielumiekan osumaan, ja hänen keskittymistään ei voi "
                   "katkaista vahingolla ilman DC 25 -tarkistusta. "
                   "Kestää minuutin.",
                   0, "", 0, "", action_type="bonus"),
            Action("Toinen loitsu",
                   "Archmage Supreme: yksi loitsu bonustoimintona samalla "
                   "vuorolla kuin toimintoloitsu. Kumpikaan ei saa olla "
                   "9. tasoa.",
                   0, "", 0, "", action_type="bonus", range=150),
            Action("Kruunun juonti",
                   "Cazna imee elinvoimaa Tarquvasin vangitusta sielusta: "
                   "palauttaa 60 HP. Tarquvas huutaa — kaikki 30 ft "
                   "sisällä tekevät DC 25 WIS -pelastuksen tai ovat "
                   "Frightened kierroksen loppuun.",
                   0, "", 0, "", action_type="bonus", range=30),
        ],
        reactions=[
            Action("Sielukoneen siirto",
                   "Kun Cazna ottaisi vahinkoa Aterterrassa, hän siirtää "
                   "sen sielukoneen vangitsemiin sieluihin: hän ottaa "
                   "0 vahinkoa. Sielukone kestää tämän 5 kertaa per "
                   "taistelu; jokainen siirto tappaa 1d100 vangittua "
                   "sielua ja koneen kristalli säröilee näkyvästi.",
                   0, "", 0, "", action_type="reaction"),
            Action("Counterspell",
                   "Reaktio: peruuttaa loitsun. Caznalla on tähän "
                   "automaattinen onnistuminen 6. tasoon asti.",
                   0, "", 0, "", action_type="reaction", range=60),
            Action("Silvery Barbs",
                   "Reaktio: pakottaa onnistuneen heiton uusiksi ja antaa "
                   "liittolaiselle edun.",
                   0, "", 0, "", action_type="reaction", range=60),
        ],
        features=[
            Feature("Legendary Resistance",
                    "5/päivä: valitse onnistuvasi epäonnistuneessa "
                    "pelastusheitossa.",
                    feature_type="passive", uses_per_day=5),
            Feature("Magic Resistance",
                    "Etu pelastusheittoihin loitsuja ja maagisia "
                    "vaikutuksia vastaan.", mechanic="magic_resistance"),
            Feature("Vanqurionin sielukone",
                    "NIIN KAUAN KUIN CAZNA ON ATERTERRASSA hän voi "
                    "reaktiolla tai legendaarisella toiminnolla siirtää "
                    "koko ottamansa vahingon Kristallijärven pohjassa "
                    "olevan Sarrukh-sielukoneen vangitsemiin satojen "
                    "tuhansien sieluihin. Pelaajien ON katkaistava tämä "
                    "yhteys ennen kuin Caznaa voi oikeasti vahingoittaa. "
                    "Kone kestää 5 siirtoa per taistelu; sen jälkeen "
                    "kristalli halkeaa ja Cazna ottaa vahingon itse. "
                    "Yhteys katkeaa myös jos ryhmä tuhoaa Kristallijärven "
                    "ankkurikristallin (AC 22, 150 HP, immuuni "
                    "psychicille) tai vie Caznan pois Aterterrasta "
                    "(Banishment, Plane Shift, Forcecage ei riitä).",
                    feature_type="passive", aura_radius=0),
            Feature("Archmage Supreme",
                    "Cazna loitsii KAKSI loitsua samalla vuorolla: yhden "
                    "toimintona ja yhden bonustoimintona. Kumpikaan ei saa "
                    "olla 9. tasoa. Hänellä on kaksi 9. tason "
                    "loitsupaikkaa.",
                    feature_type="passive"),
            Feature("Tarquvasin kruunu",
                    "Kruunun vihreään timanttiin on vangittu keisari "
                    "Tarquvas Redfein sielu (Imprisonment, astraalimeren "
                    "ikuisuusvankila). Kruunu säteilee kauhua: aura 60 ft, "
                    "jokainen vihollinen tekee vuoronsa alussa DC 25 WIS "
                    "-pelastuksen tai on Frightened vuoronsa loppuun. "
                    "Cazna voi juoda kruunusta elinvoimaa (bonustoiminto) "
                    "tai pakottaa vihollisen näkemään Tarquvasin muistot. "
                    "JOS KRUUNU TUHOTAAN, Tarquvas vapautuu — se on "
                    "kampanjan pahin mahdollinen lopputulos.",
                    aura_radius=60, save_dc=25, save_ability="Wisdom",
                    applies_condition="Frightened"),
            Feature("Kolmen ja puolen tuhannen vuoden miekkamestari",
                    "Cazna ei ole avuton lähitaistelussa — hän on "
                    "harjoitellut miekkaa 3 500 vuotta. Hän on "
                    "bladesinger: hän lyö sielumiekallaan ja loitsii "
                    "samalla vuorolla, hänen miekkaiskunsa lasketaan "
                    "maagisiksi, eikä lähitaisteluun sitominen estä häntä "
                    "loitsimasta (ei disadvantagea, ei opportunity attack "
                    "-riskiä Misty Stepistä).",
                    feature_type="passive", mechanic="extra_attack"),
            Feature("Terälaulu (Bladesong)",
                    "Bonustoiminto, 2/lyhyt lepo, kestää minuutin: +9 AC, "
                    "etu Acrobaticsiin, +1d8 force sielumiekan osumiin, "
                    "keskittyminen katkeaa vahingosta vain DC 25 "
                    "-tarkistuksen epäonnistuessa.",
                    feature_type="bonus", uses_per_day=2,
                    short_rest_recharge=True),
            Feature("Sieluvaraston magia",
                    "Miljoonien sielujen varastoitu magia: kun olento "
                    "kuolee 60 ft sisällä, Cazna palauttaa yhden käytetyn "
                    "loitsupaikan (max 7. taso) ja saa 20 temp HP.",
                    feature_type="passive"),
            Feature("Kruunun taakka",
                    "Huutava kruunu maksaa: vuoronsa alussa Cazna ottaa "
                    "10 psychic -vahinkoa (ohitetaan jos hänellä on "
                    "temp HP). Hän ei ole paha pahuudesta vaan kosmisesta "
                    "PTSD:stä — hän kuulee kahlitun titaanin huudon "
                    "jatkuvasti.",
                    feature_type="passive"),
            Feature("Foresight (Mythic Trait)",
                    "Kun sielukoneen siirrot ovat loppu JA Caznan HP "
                    "putoaa alle puoleen, hän rikkoo säännöt: aika "
                    "hidastuu hänen ympärillään. Loppu taistelun ajan hän "
                    "saa 3 YLIMÄÄRÄISTÄ REAKTIOTA per kierros (eli neljä "
                    "Counterspellia/Shieldiä kierroksessa) ja "
                    "Foresight-tilan: etu kaikkiin osumaheittoihin, "
                    "kykytesteihin ja pelastusheittoihin, ja vihollisilla "
                    "haitta osumaheittoihin häntä vastaan. Tämä on toinen "
                    "vaihe (mythic encounter, 2× XP).",
                    feature_type="passive",
                    phase_trigger_hp_pct=0.5,
                    phase_description="Aika hidastuu: 3 ylimääräistä "
                                      "reaktiota + Foresight."),
            Feature("Sielujen purkaus", "Recharge 5-6.", recharge="5-6"),
            Feature("Reaktio: Sielukoneen siirto",
                    "Ks. reaktiot. 5 kertaa per taistelu, vain "
                    "Aterterrassa.", feature_type="reaction"),
            Feature("Legendaarinen: Loitsu",
                    "Legendaarinen toiminto (1): loitsii yhden cantripin "
                    "tai 1.-3. tason loitsun.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Varjoaskel",
                    "Legendaarinen toiminto (1): teleporttaa 60 ft "
                    "(Misty Step) provosoimatta.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Sielunjuonti",
                    "Legendaarinen toiminto (2): kaikki 20 ft sisällä "
                    "tekevät DC 25 CON -pelastuksen tai ottavat 6d8 "
                    "necrotic (puolet onnistuneella); Cazna paranee "
                    "puolet kokonaisvahingosta.",
                    feature_type="legendary", legendary_cost=2,
                    damage_dice="6d8", damage_type="necrotic", save_dc=25,
                    save_ability="Constitution"),
            Feature("Legendaarinen: Koneen kuiskaus",
                    "Legendaarinen toiminto (2): siirtää vahingon "
                    "sielukoneeseen ilman reaktiota (kuluttaa yhden "
                    "koneen viidestä siirrosta).",
                    feature_type="legendary", legendary_cost=2),
            Feature("Lair: Faerzress-muuri",
                    "Lair-toiminto (init 20): 60 ft pitkä Faerzress-muuri "
                    "nousee Kristallijärven palatsissa. Täysi näkösuoja, "
                    "ja sen läpi kulkeva ottaa 5d10 force.",
                    feature_type="lair"),
            Feature("Lair: Syvyyden kaste",
                    "Lair-toiminto (init 20): yksi olento 60 ft sisällä "
                    "tekee DC 25 STR -pelastuksen tai putoaa "
                    "Kristallijärven kuiluun (10d10 vahinkoa ja "
                    "Restrained sielukoneen tentakkeleihin).",
                    feature_type="lair"),
            Feature("Lair: Kahlitun titaanin huuto",
                    "Lair-toiminto (init 20): Garruthan huuto kaikuu "
                    "kristallien läpi. Kaikki paitsi puhdasveriset drowt "
                    "tekevät DC 25 WIS -pelastuksen tai ottavat 4d10 "
                    "psychic ja ovat Frightened kierroksen loppuun.",
                    feature_type="lair"),
        ],
        legendary_action_count=3, legendary_resistance_count=5,
        items=[
            Item("Tarquvasin sielukruunu", item_type="helm", slot="helm",
                 equipped=True, rarity="artifact",
                 requires_attunement=True, attuned=True,
                 description="Kristallikruunu, jonka vihreään timanttiin on "
                             "vangittu keisari Tarquvas Redfein sielu. "
                             "Ikuisuuden vankila astraalimerellä: haavat "
                             "eivät sulkeudu, mutta kuolema ei tule. Säteilee "
                             "kauhua 60 ft. Jos kruunu tuhotaan, keisari "
                             "vapautuu."),
            Item("Icharydin sielumiekka", item_type="weapon",
                 slot="main_hand", equipped=True, rarity="legendary",
                 requires_attunement=True, attuned=True,
                 damage_dice="2d8+3d10",
                 description="Ohut drow-terä, joka on juonut sieluja 3 500 "
                             "vuoden ajan. Osumalla Cazna saa 10 temp HP ja "
                             "kohteen max HP laskee. Terälaulun kanssa "
                             "+1d8 force."),
            Item("Mage Armor -viitta", item_type="cloak", slot="cloak",
                 equipped=True, rarity="very_rare", ac_bonus=3,
                 description="Faerzress-kudottu viitta, joka pitää Mage "
                             "Armorin päällä ilman loitsupaikkaa."),
            Item("Sielukoneen ankkurikristalli (linkki)",
                 item_type="wondrous", equipped=True, rarity="artifact",
                 description="Ei esine vaan yhteys: Caznan ranteessa oleva "
                             "kristallisirpale sitoo hänet Vanqurionin "
                             "Sarrukh-sielukoneeseen Kristallijärven "
                             "pohjassa. Sirpaleen murskaaminen (DC 25, "
                             "toiminto lähietäisyydeltä) katkaisee "
                             "vahingonsiirron."),
        ],
        lore="Aterterran ikuinen hallitsija, yli 3 500 vuotta vanha "
             "arkkimaagi ja Talo Icharydin matriarkka. Hänen ja hänen "
             "sukunsa kuolemattomuus — ja käsittämätön taistelukokemus — "
             "perustuu Vanqurionin muinaiseen Sarrukh-sielukoneeseen, joka "
             "imee satojen tuhansien kuolevien sieluja heidän voimakseen. "
             "Cazna on ainoa, joka kuulee Faerzressin läpi kahlitun "
             "titaanin huudon sellaisena kuin se on: muut puhdasveriset "
             "drowt kuulevat sen kauniina 'Syvyyden Unena'. Hän ei ole paha "
             "pahuudesta vaan kosmisesta PTSD:stä. Kun Tarquvas katsoi "
             "häntä silmiin ja kertoi tietävänsä sielukoneesta ja titaanin "
             "tuskasta, Cazna kauhistui — keisari aikoi tuhota drowien "
             "kuolemattomuuden lähteen ja heidän uskontonsa valheen. Cazna "
             "ei voittanut Tarquvasia yksin: hän liittoutui Arkkimaagi "
             "Esmerin ja Cunaen Vendilien kanssa, Dimerius Blackfeet petti "
             "keisarin ratkaisevalla hetkellä, ja Cazna iski viimeisen "
             "iskun lukiten Tarquvasin sielun kruununsa vihreään "
             "timanttiin.",
        tactics="Cazna ei ota iskuja vastaan — hän vääntää säännöt. "
                "Ennen taistelua: Mage Armor, Foresight jos hänellä oli "
                "aikaa valmistautua. Kierros 1: Terälaulu bonustoimintona "
                "ja Wall of Force / Forcecage jakamaan ryhmän kahtia. "
                "Kierros 2+: Archmage Supreme = kaksi loitsua per vuoro; "
                "yhdistä Sielujen purkaus (ohittaa immuniteetit) + "
                "Misty Step pois lähitaistelusta. Käytä reaktiot "
                "Counterspelliin ja Shieldiin ARMOTTA — hän peruuttaa "
                "lähes kaiken. Muista Sielukoneen siirto: Aterterrassa "
                "ensimmäiset 5 vahinkoa ovat NOLLA. Kerro pelaajille että "
                "isku 'katoaa kristallien hehkuun' — heidän on "
                "keksittävä katkaista yhteys (ankkurikristalli tai viedä "
                "Cazna pois tasolta). Alle puolessa HP:ssä mythic-vaihe: "
                "3 ylimääräistä reaktiota ja Foresight. Jos taistelu on "
                "hävitty, hän Plane Shiftaa pois — kruunua hän ei jätä "
                "koskaan.",
        loot_table="Tarquvasin sielukruunu (kampanjan vaarallisin "
                   "artefakti — sen tuhoaminen vapauttaa keisarin), "
                   "Icharydin sielumiekka, Mage Armor -viitta, "
                   "sielukoneen ankkurikristalli, Talo Icharydin arkistot "
                   "(Garruthan totuus kirjallisena).",
        habitat="Underdark / Zer'tath Lanke / Kristallijärven palatsi",
        challenge_rating=26.0, xp=90000, proficiency_bonus=8),
]
