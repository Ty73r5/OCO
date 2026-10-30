"""THE BREATHING PLANET — scene-by-scene script.

Each scene: id, chapter, visual (renderer name + params) and narration.
Narration is written for the ear (numbers and years spelled out for the voice);
on-screen text carries the exact figures.
"""

TITLE = "THE BREATHING PLANET"
SUBTITLE = "Orbiting Carbon Observatory and the hunt for Earth's carbon"

CHAPTERS = {
    0: "",
    1: "I · The Curve",
    2: "II · A Failure, and a Second Chance",
    3: "III · Weighing the Air from Space",
    4: "IV · The Planet Breathes",
    5: "V · The Year the Tropics Exhaled",
    6: "VI · Fingerprints",
    7: "VII · The Other Carbon",
    8: "VIII · Who Put It There",
    9: "IX · Where Half of It Goes",
    10: "X · The Heat",
    11: "XI · One Day on Earth",
    12: "XII · The Watch Continues",
}

S = []


def sc(id, ch, visual, text="", hold=0.0, **params):
    S.append(dict(id=id, chapter=ch, visual=visual, params=params, text=" ".join(text.split()), hold=hold))


# ───────────────────────────── COLD OPEN ─────────────────────────────
sc("open_black", 0, "starfield", "", hold=4.0)
sc("open_earth", 0, "goes_day", """
This is our planet, exactly as it looked on the twenty third of September,
twenty twenty six, the day of the equinox, photographed every thirty minutes by a weather satellite
parked thirty six thousand kilometers above the equator.
""", start=8.0, rate=1.0, zoom=0.92)
sc("open_invisible", 0, "goes_day", """
Clouds. Storms. A great swirling storm off the coast of Mexico. Daylight sweeping across two continents.
Everything you can see here is real. But the most important thing happening in this picture
is something you cannot see at all.
""", start=22.0, rate=0.8, zoom=1.0, zoom1=1.12)
sc("open_gas", 0, "goes_day", """
Wrapped around this world is a thin layer of gas. Mixed into it, at a concentration of
roughly four hundred and thirty molecules in every million, is carbon dioxide.
It has no color and no smell. It is the breath of every animal and the food of every plant.
And over the last century and a half, we have changed its amount faster than at any time
in the geological record that ice cores can read.
""", start=33.0, rate=0.5, zoom=1.12, zoom1=1.3)
sc("open_counter", 0, "counter_intro", """
Here is a number to keep in mind. Human activity now releases about forty three billion
tonnes of carbon dioxide every year. That is close to fourteen hundred tonnes every second.
In the corner of your screen, a counter has just started. It shows how much carbon dioxide
humanity releases while you watch this film.
""")
sc("open_question", 0, "globe", """
Where does all of it go? Who releases it? Which forests and oceans are absorbing it,
and which ones are giving up? For most of history, these were questions nobody could answer,
because nobody could see the whole planet at once.
So NASA built a machine to weigh the air. From space.
""", lon0=-40, lon1=40, lat=15, dist=3.2, dist1=2.4, night=0.0)
sc("title", 0, "title", "", hold=7.0)

# ───────────────────────────── I · THE CURVE ─────────────────────────────
sc("c1_card", 1, "chapter_card", "", hold=3.5)
sc("c1_keeling_intro", 1, "globe", """
The story begins on a volcano. In March of nineteen fifty eight, a young chemist named
Charles David Keeling began measuring carbon dioxide at a small station high on the slopes of
Mauna Loa, in Hawaii. He chose it because the air there, more than three thousand meters up
and thousands of kilometers from any continent, is about as clean and well mixed as air on Earth gets.
""", lon0=-175, lon1=-150, lat=19.5, dist=2.6, dist1=1.6, marker=(-155.58, 19.54, "Mauna Loa Observatory", "3,397 m"))
sc("c1_first", 1, "keeling", """
His very first monthly average was three hundred and fifteen point seven parts per million.
Within a couple of years, he noticed two things. The first was a rhythm. Every spring the level fell,
and every autumn it rose again, like breathing.
""", t0=1958.0, t1=1962.5, ylim=(310, 324), mode="draw")
sc("c1_trend", 1, "keeling", """
The second thing was quieter, and far more important. Underneath the breathing, each year's
average sat a little higher than the last. Keeling kept measuring. His son Ralph took over the record.
NOAA built its own instruments beside it. The measurements have never stopped.
""", t0=1958.0, t1=1985.0, ylim=(310, 350), mode="draw")
sc("c1_full", 1, "keeling", """
This is what nearly seventy years of patience looks like. Every point on this line is a monthly
average of real measurements from Mauna Loa. It is called the Keeling Curve, and it may be the most
important graph of the modern age.
""", t0=1958.0, t1=2026.7, ylim=(305, 440), mode="draw")
sc("c1_global", 1, "keeling", """
And it is not just Hawaii. NOAA's global network of sampling sites, from the Arctic to the South Pole, tells the same story.
The thinner line here is the global average at the surface, starting in nineteen seventy nine. It tracks Mauna Loa almost perfectly,
with a smaller seasonal swing because it blends both hemispheres together.
""", t0=1975.0, t1=2026.7, ylim=(325, 440), mode="full", glob=True)
sc("c1_latest", 1, "keeling", """
In May of twenty twenty six, the monthly average reached four hundred and thirty two point three
parts per million, the highest ever recorded there. That is thirty seven percent more than when
Keeling started, and more than fifty percent above the level before the industrial revolution.
""", t0=1958.0, t1=2026.7, ylim=(270, 440), mode="full", preind=True, callout="latest")
sc("c1_ice", 1, "text_card", """
For context, air bubbles trapped in Antarctic ice tell us carbon dioxide stayed between
roughly one hundred and eighty and three hundred parts per million for at least eight hundred thousand years.
It rose and fell with the ice ages, slowly, over thousands of years.
We have pushed it far outside that range in about a century and a half.
""", lines=["Ice cores: ~180–300 ppm for 800,000 years", "Before industry: ~280 ppm", "May 2026, Mauna Loa: 432.3 ppm"])
sc("c1_ppm", 1, "ppm_grid", """
Parts per million can sound tiny. Picture a million marbles. Four hundred and thirty of them are
carbon dioxide. Before the industrial age it was two hundred and eighty. That small handful of extra marbles,
spread through the entire atmosphere, adds up to hundreds of billions of tonnes of extra carbon,
and it is enough to change how much heat the planet holds onto.
""")
sc("c1_blind", 1, "stations", """
But there is a problem with a curve measured on one mountain. It tells you the total is rising.
It cannot tell you where the carbon is coming from, or where it is going. Ground stations grew into a global
network, but they are sparse. Most sit in North America, Europe and on remote islands.
Over the Amazon, Central Africa, Siberia and the open ocean, there were vast regions where almost nobody was measuring.
To see the whole planet breathe, you would have to leave it.
""")

# ───────────────────── II · A FAILURE, AND A SECOND CHANCE ─────────────────────
sc("c2_card", 2, "chapter_card", "", hold=3.5)
sc("c2_oco1", 2, "timeline", """
The first attempt ended within minutes. On the twenty fourth of February,
two thousand nine, NASA's original Orbiting Carbon Observatory lifted off from Vandenberg in California
on a Taurus rocket. The protective nose cone, the fairing, was supposed to split open and fall away.
It never separated. Weighed down by the extra mass, the rocket could not reach orbit, and the
observatory fell into the ocean near Antarctica.
""", focus="2009")
sc("c2_rebuild", 2, "text_card", """
Years of work were gone in minutes. But the science case had not changed, and the team had not given up.
NASA approved a near copy, built largely to the same design, with lessons from the loss folded in.
They called it O C O two.
""", lines=["24 Feb 2009 — OCO lost: fairing failed to separate", "Rebuild approved: same design, lessons learned", "OCO-2: a near-identical second chance"])
sc("c2_launch", 2, "launch", """
At two fifty six in the morning, on the second of July, twenty fourteen, a Delta Two rocket climbed out of
Vandenberg into the dark. This time, the fairing opened. Less than an hour later, O C O two separated from the rocket
and unfolded its solar panels. The second chance had worked.
""")
sc("c2_orbit", 2, "globe", """
O C O two flies seven hundred and five kilometers up, in a polar orbit that carries it almost from pole to pole,
once every ninety nine minutes. As Earth turns beneath it, each pass crosses a new strip of the planet.
""", lon0=-100, lon1=-60, lat=10, dist=3.0, dist1=3.0, orbit="oco2", orbit_hours=(0, 0.1), sat=True, trail=True)
sc("c2_tracks", 2, "globe", """
Watch how the tracks build up. About fourteen and a half orbits a day. After sixteen days, two hundred
and thirty three orbits, the pattern repeats exactly. This is a sun synchronous orbit: the satellite always
crosses the equator at about one thirty six in the afternoon local time, when the Sun is high
and the light reflected from the ground is strongest.
""", lon0=-60, lon1=200, lat=20, dist=3.3, dist1=3.3, orbit="oco2", orbit_hours=(0, 72), sat=True, trail=True, tracks=True)
sc("c2_atrain", 2, "atrain", """
For most of its life, O C O two has flown at the head of a formation that scientists nicknamed the A Train:
a line of Earth observing satellites crossing the same ground minutes apart, so that measurements of clouds, aerosols,
water vapor and carbon can be stitched together into one picture of the same moment.
""")

# ───────────────────── III · WEIGHING THE AIR FROM SPACE ─────────────────────
sc("c3_card", 3, "chapter_card", "", hold=3.5)
sc("c3_light", 3, "lightpath", """
So how do you measure a gas you cannot see, through the whole depth of the atmosphere, from seven hundred kilometers away?
You use sunlight. Sunlight passes down through the air, reflects off the ground, and travels back up through the air
to the satellite. Twice through the atmosphere. Along the way, every carbon dioxide molecule it meets can absorb a little of it.
""")
sc("c3_barcode", 3, "spectrum", """
But molecules are picky. Carbon dioxide only absorbs light at very specific wavelengths, set by the way its atoms vibrate and rotate.
Spread sunlight out finely enough and those wavelengths show up as dark lines, a pattern as distinctive as a barcode.
The more carbon dioxide the light passed through, the deeper those lines become.
""", band="co2", stage="lines")
sc("c3_three", 3, "spectrum", """
O C O two carries three spectrometers that share one telescope. One looks at carbon dioxide near one point six one microns.
One looks at a stronger carbon dioxide band near two point zero six microns. And the third looks at oxygen, near zero point seven six microns.
Each splits the light into more than a thousand separate colors.
""", band="three", stage="bands")
sc("c3_oxygen", 3, "spectrum", """
Why oxygen? Because oxygen is the ruler. It makes up a steady twenty point nine five percent of dry air everywhere on Earth.
So the oxygen lines reveal exactly how much air the light passed through, mountains or sea level, clear sky or haze.
Divide the carbon dioxide signal by the amount of air, and you get the quantity scientists call X C O two:
the average concentration of carbon dioxide in the entire column of air, from the ground to the edge of space.
""", band="o2", stage="ratio")
sc("c3_precision", 3, "precision", """
And it has to be extraordinarily precise. Carbon sources and sinks change that column by only a few parts per million out of more than four hundred.
To be useful, each measurement needs a precision of about one part per million, roughly a quarter of one percent.
That is like weighing a full suitcase so accurately that you notice someone slipped in a single extra sock.
""")
sc("c3_footprints", 3, "footprints", """
The instrument records three frames every second. Each frame captures eight side by side footprints,
each about one point three kilometers wide and two and a quarter kilometers long, together forming a swath roughly ten kilometers wide.
Twenty four measurements per second, on the sunlit side of every orbit.
""")
sc("c3_million", 3, "million", """
That adds up to roughly a million measurements a day. But many are spoiled by clouds or thick haze,
because the light has to reach the ground and come back cleanly. After strict screening, a much smaller set,
typically on the order of a hundred thousand good soundings a day, goes into the best quality data.
Even so, that is more than every ground station on Earth combined could ever collect.
""")
sc("c3_retrieval", 3, "retrieval", """
Turning those spectra into a single number is a feat of physics. For every sounding, a computer model simulates how sunlight would travel through the atmosphere,
accounting for surface pressure, temperature, water vapor, clouds and tiny airborne particles. It adjusts all of them until the simulated spectrum matches
the measured one line for line. What remains is the carbon dioxide. Then the results are checked, and corrected for small biases,
against independent measurements made from the ground.
""")
sc("c3_modes", 3, "modes", """
Over land, O C O two can look straight down at the ground beneath it. Over the dark ocean it tilts toward the bright spot where sunlight glints off the water,
to catch enough light. And regularly it stares at one place while flying past, locking onto ground stations of the
Total Carbon Column Observing Network, so that every satellite measurement can be checked against instruments on the surface.
""")
sc("c3_sif", 3, "sif", """
Then came a bonus nobody had planned the mission around. When plants photosynthesize, their chlorophyll re-emits a tiny fraction
of the absorbed sunlight as a faint red glow, called solar induced fluorescence. It is far too weak to see with your eyes,
but inside the dark Fraunhofer lines of the solar spectrum, where sunlight is nearly absent, O C O two can detect it. For the first time, scientists could watch photosynthesis itself,
the planet actually inhaling, from orbit.
""")

# ───────────────────────── IV · THE PLANET BREATHES ─────────────────────────
sc("c4_card", 4, "chapter_card", "", hold=3.5)
sc("c4_season", 4, "seasonal", """
Remember Keeling's rhythm? Here it is, isolated. Take away the long term rise, and the Mauna Loa record shows the same yearly breath,
peaking in May and bottoming out around September or October. Each line is a different era.
""")
sc("c4_why", 4, "globe", """
The reason is geography. Most of Earth's land, and most of its forests, lie in the Northern Hemisphere.
Every northern spring, billions of trees leaf out across North America, Europe and Siberia and pull carbon dioxide out of the air.
Every autumn, the leaves fall and decay, and the carbon comes back. The whole hemisphere inhales in summer and exhales in winter.
""", lon0=40, lon1=120, lat=50, dist=2.8, dist1=2.6, tilt_north=True)
sc("c4_amp", 4, "amplitude", """
And the breath itself is changing. At Mauna Loa, the swing between the spring peak and the autumn low has grown over the decades,
from under six parts per million in the nineteen sixties to more than six and a half today. Far to the north, in Alaska and the Arctic,
the yearly swing is much larger still, and has grown faster. Northern ecosystems are breathing more deeply in a warmer, carbon rich world.
""")
sc("c4_south", 4, "keeling", """
In the Southern Hemisphere, which is mostly ocean, the breathing is much fainter. At the South Pole, the yearly swing is only around a single part per million.
The planet's breath is lopsided, and the satellite sees that asymmetry every single day, sweeping from pole to pole.
""", t0=2015.0, t1=2026.7, ylim=(395, 436), mode="full", glob=True)
sc("c4_growth", 4, "growth_bars", """
Now look at how fast the total has been rising, year by year. In the early nineteen sixties, Mauna Loa's annual average rose by less than one part per million each year.
In the twenty tens, it was close to two and a half. In twenty twenty four, it jumped by three and a half: the largest annual rise in the record.
""")
sc("c4_wobble", 4, "growth_bars", """
Notice that the bars are not smooth. Some years leap upward, like nineteen ninety eight, twenty sixteen and twenty twenty four.
Human emissions do not swing that much from year to year. Something in nature is changing how much carbon the planet absorbs.
That something has a name. And it was O C O two that showed us, continent by continent, how it works.
""", highlight=[1998, 2016, 2024])

# ───────────────────── V · THE YEAR THE TROPICS EXHALED ─────────────────────
sc("c5_card", 5, "chapter_card", "", hold=3.5)
sc("c5_sst1", 5, "sst", """
In twenty fifteen, a giant pool of unusually warm water spread across the tropical Pacific. This is real data from NOAA:
satellite and buoy measurements of sea surface temperature, shown as the difference from normal.
Red is warmer than usual. Watch the equatorial Pacific.
""", d0="2014-06-01", d1="2015-06-30")
sc("c5_sst2", 5, "sst", """
This is El Niño, and the one of twenty fifteen and twenty sixteen was among the strongest ever measured.
It reshuffles weather around the world, bringing drought and heat to some regions and floods to others.
And it arrived just as O C O two had begun sending back its first full year of data.
""", d0="2015-07-01", d1="2016-03-31")
sc("c5_result", 5, "tropics", """
In twenty seventeen, the mission's scientists published a set of studies in the journal Science.
By comparing twenty fifteen with the calmer year of twenty eleven, they found that the tropical land regions of the world released about
two and a half billion tonnes more carbon into the atmosphere during the El Niño year.
That extra pulse helped push the global growth rate of carbon dioxide to a record at the time.
""", stage=0)
sc("c5_three", 5, "tropics", """
The surprise was that the three tropical continents did it in three different ways. In South America, severe drought meant the rainforest
photosynthesized less, so it absorbed less carbon. In Africa, rainfall was near normal but higher temperatures sped up decay,
so soils and plants breathed out more. And in Indonesia, drought dried out carbon rich peatlands, and fires released enormous amounts of carbon.
Same El Niño. Three different responses.
""", stage=1)
sc("c5_meaning", 5, "growth_bars", """
This is exactly the kind of insight a single mountaintop could never provide. The curve at Mauna Loa told us that something happened.
The satellite told us where, and suggested why. And it carries a warning: in a hotter, drier future, the tropical forests that have long absorbed
part of our emissions could absorb less, or even turn into sources.
""", highlight=[1998, 2016, 2024], focus=(2010, 2025))

# ───────────────────────── VI · FINGERPRINTS ─────────────────────────
sc("c6_card", 6, "chapter_card", "", hold=3.5)
sc("c6_cities", 6, "no2", """
Carbon dioxide from a power plant or a city is quickly diluted into the global background, which makes it fiendishly hard to spot from space.
But burning fossil fuel releases other gases at the same time. This is nitrogen dioxide, measured by the European TROPOMI instrument on the
Sentinel five P satellite over the winter of twenty twenty four to twenty twenty five. Every bright patch is combustion: traffic, industry, power stations.
""", region="world")
sc("c6_cities2", 6, "no2", """
Zoom in, and the map becomes a portrait of human activity. The industrial heart of Europe. The Indo Gangetic plain. Eastern China.
Nitrogen dioxide lasts only hours, so it stays close to where it was emitted, a fingerprint pointing at the source.
Scientists now pair these maps with carbon dioxide measurements to estimate how much carbon each hot spot releases.
""", region="tour")
sc("c6_plants", 6, "text_card", """
O C O two was never designed to measure individual smokestacks. Yet when its narrow swath happened to pass directly over a large coal power plant,
researchers could pick out the plume as a small bump in carbon dioxide, a few parts per million above the surroundings,
and use it to estimate the plant's emissions. It was proof that power plants could be checked from orbit.
""", lines=["Single power-plant plumes detected from orbit", "Urban CO₂ domes over cities", "Volcanic CO₂ seen from space"])
sc("c6_la", 6, "la_dome", """
The same team measured the dome of extra carbon dioxide that sits over Los Angeles, and found it several parts per million higher than the
surrounding desert air. They even spotted carbon dioxide from the Yasur volcano in the South Pacific, a measurement that could one day
help warn of eruptions, since volcanoes often release more carbon dioxide before they erupt.
""")
sc("c6_oco3", 6, "globe", """
In May of twenty nineteen, a SpaceX Dragon delivered O C O three to the International Space Station. It was built largely from O C O two's spare parts,
but with a new trick: an agile pointing mirror. Instead of a single narrow strip, it can sweep back and forth and build a snapshot map of an entire city,
roughly eighty by eighty kilometers, in about two minutes.
""", lon0=-130, lon1=-60, lat=20, dist=3.0, dist1=2.6, orbit="iss", orbit_hours=(0, 6), sat=True, trail=True)
sc("c6_iss", 6, "globe", """
The space station's orbit is different, too. It is not sun synchronous, so O C O three passes over the same places at different times of day:
morning traffic, afternoon heat, evening rush. It covers the band of the planet between about fifty two degrees north and south,
where most of humanity lives.
""", lon0=-60, lon1=120, lat=10, dist=3.3, dist1=3.3, orbit="iss", orbit_hours=(0, 48), sat=True, trail=True, tracks=True)

# ───────────────────────── VII · THE OTHER CARBON ─────────────────────────
sc("c7_card", 7, "chapter_card", "", hold=3.5)
sc("c7_ch4", 7, "ch4", """
Carbon dioxide is not the only carbon gas we are changing. Methane, the main ingredient of natural gas, traps about eighty times more heat than carbon dioxide
over its first twenty years in the air. Its concentration has more than doubled since before the industrial age.
This map is real: measurements spanning six months of twenty twenty four from the TROPOMI instrument, averaged together.
""", region="world")
sc("c7_ch4b", 7, "ch4", """
The hot spots tell stories. Rice paddies and wetlands across South and East Asia. The vast swamps of the Sudd in South Sudan.
But not every bright patch is real. Over the Sahara, very bright desert sand fools this uncorrected product into reading high,
which is exactly why scientists spend years on careful corrections. Methane does not last as long as carbon dioxide, only about a decade,
which makes cutting it one of the fastest ways to slow warming.
""", region="tour")
sc("c7_super", 7, "text_card", """
Satellites have also found something more alarming: super emitters. Single leaking wells, pipelines and landfills that release methane at rates of tons per hour.
Some have been spotted from orbit, reported, and then repaired. Fixing a leak you can see from space is among the cheapest climate wins there is.
""", lines=["Super-emitters: single sites leaking tonnes of methane per hour", "Spotted from orbit → reported → repaired", "~80× the warming of CO₂ over 20 years"])
sc("c7_fire_intro", 7, "co_fire", """
Now watch carbon monoxide, a gas released when things burn incompletely. In late May and June of twenty twenty three, Canada was on fire.
Each frame of this sequence is one day of real satellite measurements over North America.
""", stage="intro")
sc("c7_fire", 7, "co_fire", """
Smoke from hundreds of fires in Quebec and the West poured south and east. On the seventh of June, it buried New York City in an orange haze,
and the air quality there briefly ranked among the worst of any major city on Earth. The plumes crossed the Atlantic and reached Europe.
""", stage="anim")
sc("c7_fire_total", 7, "fire_total", """
That season, more than fifteen million hectares of Canadian forest burned. Using satellite measurements of carbon monoxide,
a study published in Nature estimated that the fires released around six hundred and fifty million tonnes of carbon.
That is more than the annual fossil fuel emissions of every country on Earth except China, India and the United States.
""")
sc("c7_feedback", 7, "text_card", """
This is what scientists mean by a feedback. Warming dries out forests. Dry forests burn. Burning forests release carbon. More carbon means more warming.
Satellites are how we find out how strong that loop is becoming.
""", lines=["Warming → drier forests", "Drier forests → more fire", "More fire → more carbon", "More carbon → more warming"])

# ───────────────────────── VIII · WHO PUT IT THERE ─────────────────────────
sc("c8_card", 8, "chapter_card", "", hold=3.5)
sc("c8_global", 8, "emissions_area", """
So where does all the carbon come from? This is humanity's yearly carbon dioxide from fossil fuels and cement, going back to seventeen fifty, split by source.
For more than a century the line barely rises. Coal powered the first industrial revolution. Then oil. Then gas. And then, after nineteen fifty, everything accelerates.
""")
sc("c8_now", 8, "emissions_area", """
In twenty twenty four, fossil fuels and industry released around thirty eight and a half billion tonnes of carbon dioxide.
Add deforestation and other land use changes, and the total is about forty three billion. Half of all the fossil carbon dioxide ever emitted
has been released since the mid nineteen nineties.
""", mode="full")
sc("c8_fuels", 8, "fuel_bars", """
Break twenty twenty four down by fuel, and coal is still the biggest single source, close to sixteen billion tonnes. Oil adds about twelve and a half.
Natural gas about eight. Cement, which releases carbon dioxide from the chemistry of making it, not just the energy, adds roughly one and a half more.
""")
sc("c8_race", 8, "bar_race", """
But the atmosphere does not care who emitted carbon this year. It keeps a running total. Here is each country's cumulative emissions from fossil fuels and cement
since seventeen fifty. Watch the order change as the industrial age spreads around the world.
""")
sc("c8_race_end", 8, "bar_race", """
By twenty twenty four, the United States had emitted the most in total, around four hundred and thirty five billion tonnes.
China, now by far the largest emitter each year, is second and climbing fast. Russia, Germany and the United Kingdom, early industrial powers,
still rank near the top.
""", mode="final")
sc("c8_percap", 8, "per_capita", """
And per person, the picture changes again. The average American emits about fourteen tonnes a year. The average person in China, around eight and a half.
In India, about two point two. These differences sit at the heart of every international climate negotiation.
And this is precisely why independent measurements from space matter: the atmosphere is the one ledger nobody can edit.
""")

# ───────────────────────── IX · WHERE HALF OF IT GOES ─────────────────────────
sc("c9_card", 9, "chapter_card", "", hold=3.5)
sc("c9_budget", 9, "budget", """
Here is one of the strangest facts in all of climate science. Of all the carbon dioxide we release, only a little under half stays in the atmosphere.
The rest disappears. Scientists who balance the global carbon budget each year find that the ocean absorbs roughly a quarter of our emissions,
and land plants and soils absorb roughly another quarter to a third.
""", stage=0)
sc("c9_ocean", 9, "budget", """
The ocean takes it in by simple chemistry: carbon dioxide dissolves into cold surface water and is carried into the depths. The price is acidity.
Seawater has grown measurably more acidic since the industrial age began, which makes life harder for corals, shellfish and plankton.
""", stage=1)
sc("c9_land", 9, "budget", """
The land sink is the mysterious one. Forests and grasslands absorb billions of tonnes of carbon a year, but how much, and exactly where, swings from year to year
and has been one of the biggest uncertainties in climate science. Is it northern forests regrowing? The Amazon? Fertilization from the extra carbon dioxide itself?
""", stage=2)
sc("c9_stocktake", 9, "text_card", """
In twenty twenty three, scientists working with O C O two data published something new: estimates of carbon dioxide emissions and removals for more than one hundred countries,
derived from the atmosphere itself, as a contribution to the first global stocktake under the Paris Agreement.
Not what countries reported. What the air recorded. It is an early version of something the world has never had: an independent way to check the books.
""", lines=["2023: national CO₂ budgets from the atmosphere", "100+ countries, informed by OCO-2", "An independent check on the books"])
sc("c9_why", 9, "globe", """
These natural sinks are the reason the planet has warmed only as much as it has. They are a gift we have been receiving for free.
The question that hangs over the century is whether that gift will keep coming. That is the deepest reason missions like O C O two exist:
not just to watch our emissions, but to watch the planet's response to them.
""", lon0=-80, lon1=20, lat=-5, dist=2.9, dist1=2.5)

# ───────────────────────────── X · THE HEAT ─────────────────────────────
sc("c10_card", 10, "chapter_card", "", hold=3.5)
sc("c10_stripes", 10, "stripes", """
Why does any of this matter? Because carbon dioxide traps heat. This is NASA's record of global surface temperature, from eighteen eighty to today,
each stripe one year. Blue is cooler than the mid twentieth century average. Red is warmer.
""")
sc("c10_line", 10, "temp_line", """
Twenty twenty four was the warmest year in the record, about one point three degrees Celsius above the nineteen fifty one to nineteen eighty average,
and roughly one and a half degrees warmer than the late nineteenth century. Twenty twenty five came in second.
""")
sc("c10_paris", 10, "temp_line", """
In Paris, in twenty fifteen, the world's nations agreed to try to hold warming well below two degrees, and to pursue one and a half.
Single years have now touched that lower line. Whether the long term average crosses it depends largely on how quickly the curve you saw at the beginning of this film stops rising.
""", paris=True)
sc("c10_scatter", 10, "co2_temp", """
Plot each year's temperature against that year's carbon dioxide level, and the two climb together. Physics explains why. Carbon dioxide absorbs and re emits infrared heat
leaving the Earth's surface, something scientists first measured in the laboratory in the eighteen fifties. Add more of it, and the planet must warm until it sheds as much heat as it receives.
""")

# ───────────────────────── XI · ONE DAY ON EARTH ─────────────────────────
sc("c11_card", 11, "chapter_card", "", hold=3.5)
sc("c11_day", 11, "goes_day", """
Let us step back. This is one full day on the planet you live on, from midnight to midnight, as seen by GOES nineteen on the September equinox of twenty twenty six.
""", start=0.0, rate=1.0, zoom=1.0)
sc("c11_day_music", 11, "goes_day", "", hold=32.0, start=12.0, rate=1.12, zoom=1.0)
sc("c11_day_end", 11, "goes_day", """
Every swirl of cloud is carrying carbon dioxide with it. The atmosphere mixes the whole planet's breath together in about a year.
Which is why, to understand it, you have to watch it all, all the time.
""", start=26.0, rate=0.45, zoom=1.0, zoom1=1.25)

# ───────────────────────── XII · THE WATCH CONTINUES ─────────────────────────
sc("c12_card", 12, "chapter_card", "", hold=3.5)
sc("c12_fleet", 12, "timeline", """
O C O two was not alone, and it was never meant to be. Japan's GOSAT pioneered greenhouse gas measurements from space in two thousand nine.
China launched TanSat. Japan followed with GOSAT two, and in twenty twenty five with GOSAT G W. France launched MicroCarb that same year.
Europe is building a constellation of carbon monitoring satellites, called C O two M, for the coming years.
""", focus="fleet")
sc("c12_long", 12, "text_card", """
O C O two was designed for a two year prime mission. It has now been measuring the planet's breath for more than twelve years,
building one of the longest and most precise records of carbon dioxide ever made from space. O C O three has been at work on the space station since twenty nineteen.
""", lines=["OCO-2: 2-year prime mission → 12+ years in orbit", "OCO-3: on the ISS since 2019", "Data freely available to anyone"])
sc("c12_budget", 12, "text_card", """
In twenty twenty five, both missions were proposed for termination in the federal budget, even though both were working well and together cost on the order of
fifteen million dollars a year to operate. Scientists around the world argued that switching them off would break a record that cannot be restarted.
""", lines=["2025: termination proposed", "Operating cost: ~$15 million / year for both", "A record that cannot be restarted"])
sc("c12_caltech", 12, "text_card", """
In August of twenty twenty six, NASA signed agreements with Caltech to operate both observatories for up to five years, with NASA retaining ownership,
and operations moving to Caltech this autumn. For now, the watch continues.
""", lines=["14 Aug 2026: NASA–Caltech agreements", "Caltech operates OCO-2 and OCO-3, up to five years", "The watch continues"])
sc("c12_next", 12, "text_card", """
The next questions are already clear. Will the Amazon keep absorbing carbon, or tip toward releasing it? Will thawing Arctic permafrost release carbon frozen for thousands of years?
Will the oceans keep taking up their share? None of these can be answered by models alone. They need measurements, continuous and global, year after year.
""", lines=["Will the Amazon keep absorbing carbon?", "Will thawing permafrost release its carbon?", "Will the ocean sink keep pace?"])
sc("c12_counter", 12, "counter_final", """
Remember the counter in the corner. Since this film began, humanity has released this much carbon dioxide.
Roughly half of it will linger in the air, and part of that for centuries or longer. The rest has already started the long journey into the oceans and the forests,
for as long as they keep accepting it.
""")
sc("c12_close", 12, "goes_day", """
Somewhere above you right now, a small observatory is crossing the sunlit side of the planet, splitting sunlight into a thousand colors,
counting molecules in a column of air seven hundred kilometers tall. It sees what no one on the ground can see: a living planet,
breathing in, breathing out, and slowly changing. The more clearly we can see that, the better our chances of choosing what happens next.
""", start=30.0, rate=0.5, zoom=1.0, zoom1=0.62)
sc("credits", 12, "credits", "", hold=22.0)
