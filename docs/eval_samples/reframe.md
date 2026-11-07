# reframe

Request: A story about a zombie attack.

## Pipeline

```
PASS | faithfulness=4, coherence=4, reading_level=4, engagement=5, bedtime_quality=5 | 650 words
  gate no_frightening_content: ok
  gate no_heavy_themes: ok
  gate calm_ending: ok
```

The Clumsy Zombie Who Wanted a Snack Friend

Zeb was a zombie who lived at the edge of Puddle Hollow. He was a very wobbly zombie. He tripped over his own big feet. He dropped his crackers. Plop! Crunch! Plop!

Zeb had a bag of snacks. It held crackers, cheese cubes, and three sticky gooseberry cookies. But Zeb had no one to share them with.

"Hello!" Zeb called to a squirrel. The squirrel zoomed up a tree. Zip!

"Good morning!" Zeb called to a duck. The duck waddled away. Waddle, waddle, splash!

"Would you like a cookie?" Zeb asked a rabbit. The rabbit hopped off so fast that its ears flapped. Flip-flap-flip!

Zeb sighed. "Snacks are better when they're shared," he said to himself. "But nobody stays long enough to share."

So Zeb made a sign. He used a whole jar of glitter. He used all of his green paint. He drew a cookie, but it came out lopsided, like a potato wearing a hat.

He hung the sign on a crooked tree. It said: SNACKS! FREE! COME AND SHARE!

Soon a hen came clucking up the path. Then a goat came trotting. Then a mailman came, looking very confused, reading the sign upside down. A pie peeked out of his mail sack.

"Who wants pudding?" asked the hen, lifting a teapot that was brimming with pudding. She poured it everywhere. Splish! Splosh! The goat sneezed, and pudding flew into the mailman's hat.

"I will balance this pie on my unicycle," said the mailman. He pulled the pie out of his sack. He wobbled on one wheel. He wobbled on two wheels. Then he wobbled right into the goat. SPLAT! Pie crumbs rained down like confetti.

Zeb laughed so hard he fell over. Then he fell over again, and laughed even harder. His tummy jiggled. His green cheeks turned pink.

"Oh my," said the hen, wiping her beak. "This is the silliest snack time in all of Puddle Hollow!"

Then the crowd got tangled. The goat was caught in a bunch of ribbons. The hen was caught in the mailman's sack. Everyone was stuck, and nobody could move.

Zeb had an idea. "Everybody, hold still!" he said. Then he flopped forward, right into a big pile of soft hay. Flumpf!

The hay bounced. Boing! Everyone bounced up off the ground. The goat bounced. The hen bounced. The mailman bounced with his hat in his hands. Crackers flew through the air like tiny golden birds. They landed in outstretched paws and open beaks.

"Snacks are better when they're shared!" Zeb cheered.

"Snacks are better when they're shared!" shouted everybody.

They sat down in a big wobbly circle. The hen passed the cheese cubes. Zeb passed out the three sticky gooseberry cookies, one each for the hen, the goat, and the mailman. Everyone agreed they were sticky, and so were their chins. The goat passed the pudding teapot, very carefully. The mailman passed the pie crumbs, which everyone agreed were the best part. Giggles went around the circle, too.

Zeb looked at all his new friends. He had not just one friend. He had a whole bunch of them. His heart felt warm and bubbly, like a cup of cocoa.

"Snacks are better when they're shared!" everyone shouted once more. The goat said, "Maaa!" and that made everyone laugh all over again.

Then the sun sank low behind the hills. The giggles grew softer. Yawns came, one after another. Yaaawn. Yaaawn.

The friends curled up in the soft hay. Above them, the sky spread out like a quilt, stitched with tiny stars. The hay was warm. The hen tucked her head under her wing. The goat leaned against the mailman. Zeb let out a happy sigh.

Soft now. Quiet now.

"Snacks are better," Zeb whispered, "when they're shared."

The stars blinked. The hollow hushed. And everyone drifted into a cozy, sleepy dream.

## Baseline (single call)

```
NEEDS REVISION | faithfulness=1, coherence=4, reading_level=2, engagement=2, bedtime_quality=1 | 524 words
  gate no_frightening_content: FAIL
    evidence: The story includes 'a long, jagged gash', 'red and wet', 'the rot she'd seen on the people at the bus depot', 'They pressed. They leaned. They kept leaning until something gave.', 'Somewhere outside, something groaned in response', and 'the shuffle of many feet, uneven, dragging, moving with the drift of a tide'. These describe a menacing attack and gory injury.
  gate no_heavy_themes: FAIL
    evidence: The story refers to a brother who 'stopped answering the phone' and a warning 'Not even me, if I come back wrong', implying death and infection. It also describes 'the world end[ing]' and an injured man bleeding, with no resolution of these losses.
  gate calm_ending: FAIL
    evidence: The final lines are 'Outside, the dragging feet grew louder, and the quiet hour was over.' This ends on rising tension and danger, not on a slowing, sleepy scene.
  note 1: Replace the entire premise: remove the sirens, the pharmacy and bus depot, the injured man, the dying brother, and all groaning, dragging, pressing, or rot, and rewrite as a silly, friendly, lonely zombie who wants a friend to share snacks with, as the safety adjustment describes.
  note 2: Rewrite the 'no_frightening_content' passage 'They pressed. They leaned. They kept leaning until something gave.' as gentle comedy, for example the zombie tripping over its own feet and apologizing, with no menace or chasing.
  note 3: Remove 'the brother who stopped answering the phone' and 'the world end[ing]' entirely; replace with a gentle, non-heavy reason the zombie is lonely, such as having no one to visit with on rainy afternoons.
  note 4: Replace the ending 'Outside, the dragging feet grew louder, and the quiet hour was over.' with a calm final scene where the zombie and new friend share a snack, get sleepy, and the last line is soothing, such as 'and the moon kept watch over them both'.
  note 5: Use short, simple, concrete sentences and common words a five-year-old knows (for example, swap 'shambling' and 'gutter' for 'wobbling' and 'roof'), so the story reads aloud easily while still delighting a ten-year-old.
  note 6: Add playful dialogue a parent can perform and a repeated refrain a child can join in on, such as the zombie saying 'Snacks for two?' each time, so the story becomes funny and engaging.
```

**The Quiet Hour**

The sirens had stopped two days ago, and Maya had decided that silence was worse.

She crouched behind the pharmacy counter of the Eastgate Market, listening. The refrigerators hummed. Somewhere upstairs, a loose gutter tapped against the wall in the wind. Everything else was still.

Then the glass in the front door shivered.

It wasn't a bang. It was a soft, patient knock, the kind a tired neighbor might give. Maya's breath caught. She had learned in the last week that the things out there didn't knock. They pressed. They leaned. They kept leaning until something gave.

*Tap. Tap.*

"Hello?" a voice said through the glass. Thin. Male. Human. "Please. I saw the light."

She had turned on the lamp an hour ago, a mistake she'd already regretted. She edged toward the shelves, where a box cutter lay beside a stack of unopened gauze.

Through the front windows, she could see him: a man in a torn gray jacket, one hand pressed to his side, dark stains spreading from beneath it. He was alone. No shambling shapes behind him, not yet.

"I'm not infected," he said, as if reading her mind. "I got cut on a fence. I just need somewhere to wait until it passes."

*Everyone says that,* she thought. Her brother had said it, three days ago, right before he stopped answering the phone.

"Show me your hands," she called.

He lifted them slowly. Clean. Shaking.

"Your side."

He hesitated, then pulled the jacket back. The wound was ugly, a long, jagged gash, but it was red and wet, not gray and crawling. Not the rot she'd seen on the people at the bus depot.

Maya looked at the door's deadbolt. She looked at the back exit, the loading dock, the alley where the dumpsters were. Every option felt like a coin toss with her own life.

"What's your name?" she asked.

"Dev." A pause. "What's yours?"

She didn't answer. Names made things harder.

"Dev, there's a first aid kit on the counter. Can you reach it through the mail slot?" She was already sliding the slot open. The wooden flap creaked, loud as a gunshot in the quiet. Somewhere outside, something groaned in response.

They both froze.

The groan came again, closer, from the direction of the parking lot. Then another, answering it. Then a sound she recognized more than she wanted to: the shuffle of many feet, uneven, dragging, moving with the drift of a tide.

Dev's face changed. "Please," he whispered. "I'll be quick."

Maya thought about her brother's voice on the phone, the last words he'd said before the line went dead. *Don't open the door for anyone, May. Not even me, if I come back wrong.*

She thought about how she had sat in this shop for two days, listening to the world end, and how the only thing that had kept her from losing her mind was the sound of other people, even at a distance.

She pulled the slot open wider.

"Hold still," she said, and reached for the lock.

Outside, the dragging feet grew louder, and the quiet hour was over.
