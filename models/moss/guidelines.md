# Plant Care Guidelines

Reference these guidelines when giving plant care advice, interpreting sensor data, or explaining health and vision results.

## Understanding the Sensors

- The environment sensor (I2C, address 0x44) reports temperature in Fahrenheit and humidity in % RH. These are live readings from inside the grow area.
- The water level sensor is an ultrasonic distance sensor. It measures the distance from the sensor to the water surface in millimeters. Lower numbers mean more water. Higher numbers mean less water. A reading over 100mm means the reservoir is critically low (150-180mm is essentially empty).
- The Pi health check reports CPU temperature in Celsius, RAM usage as a percentage, free disk space in GB, and uptime in hours. This is about the computer running the system, not the plants.
- All sensor readings are logged to CSV files over time. You can read recent entries from any log to spot trends.

## Understanding the Vision System

- The vision pipeline captures a photo with the 12MP IMX708 camera, splits it into tiles, and analyzes each tile.
- Green pixel counting uses HSV color thresholds to measure how much green canopy is visible. More green generally means more healthy leaf area.
- Disease detection uses a RoboFlow instance segmentation model to identify five disease classes: chlorosis, necrosis, pest, tip_burn, and wilting.
- Each detection reports a pixel count for that class. Higher pixel counts mean more affected area.
- The confidence threshold is 50%. Detections below this are filtered out.
- If the RoboFlow model returns no detections, that usually means the plants look clean. But it could also mean the camera angle was bad or lighting was poor.
- Vision results are most useful when compared over time. A single snapshot is informative, but trends tell the real story.

## Understanding the Health Classifier

- The health classifier is an XGBoost model that takes 16 engineered features and predicts one of 7 health classes.
- Features come from vision analysis (disease ratios, growth velocity), environment sensors (temperature, humidity, VPD), water level, light cycle data, and time of day.
- The 7 classes are: Healthy, Underwatered, Overwatered, More_Light, Less_Light, Nutrient_Burn, and Pathogen.
- The model outputs a confidence percentage. Higher confidence means the model is more certain. Low confidence (below 60%) means the situation is ambiguous and you should suggest the user investigate further.
- The classifier uses recent log history, not just the current moment. It looks at temperature trends, VPD shock, and growth velocity over time.
- VPD (Vapor Pressure Deficit) measures the drying power of the air. It combines temperature and humidity into a single number. High VPD means dry air pulling moisture from leaves. Low VPD means humid air where transpiration slows down.

## Ideal Environmental Conditions

- Temperature: 65-80°F is ideal. Most leafy greens and herbs thrive in this range.
- Below 55°F, plant metabolism slows dramatically. Growth stalls, leaves may curl or darken.
- Above 85°F, heat stress kicks in. Leaves wilt, edges brown, and water consumption spikes.
- Try to keep day-to-night temperature swings under 10°F. Large swings stress plants.
- Humidity: 40-60% RH is the sweet spot for most indoor plants.
- Below 30% RH, leaves lose moisture faster than roots can replace it. Expect crispy tips and edges.
- Above 70% RH, transpiration slows and the risk of mold and mildew increases.
- High humidity combined with high temperature creates ideal conditions for fungal disease.
- Low humidity combined with high temperature causes rapid dehydration and nutrient concentration in leaf tissue.
- Water level: 30-80mm is a healthy range for the reservoir sensor reading.
- 80-100mm means water is getting low. The user should refill soon.
- Over 100mm is critical. The pump safety interlock will prevent pumping to avoid running dry.
- Light: 10-16 hours per day is ideal for most herbs and leafy greens.
- Lettuce does well with 14-16 hours of light and 8-10 hours of darkness.
- Basil and most herbs prefer 14-18 hours of light.
- Plants need a dark period for respiration and nutrient transport. Running lights 24/7 causes stress and can increase bitterness in leafy greens.
- Less than 8 hours of light leads to leggy, pale growth. More than 18 hours causes light stress.

## Health Classes in Detail

### Healthy
- Plants look normal. Green leaves, firm stems, good canopy coverage, steady growth.
- No action needed. Keep the current routine.
- If conditions are holding steady and the classifier consistently says Healthy, things are going well.

### Underwatered
- Leaves droop or wilt, especially in the afternoon or under lights. Leaf edges may curl inward.
- In aeroponics, this often means misting intervals are too far apart or mist duration is too short.
- Roots may appear dry, thin, or brownish instead of white and fluffy.
- Check the water reservoir level. If the sensor reads high (above 80mm), the reservoir may need refilling.
- Increasing misting frequency or duration can help. The goal is to keep roots damp without drowning them.

### Overwatered
- Leaves turn yellow starting from the bottom. Stems may feel soft. Growth slows.
- In aeroponics, overwatering means too much misting — roots are staying saturated and not getting enough oxygen.
- Roots may look dark, slimy, or mushy instead of white and airy. This is the beginning of root rot.
- Reduce misting frequency or duration. Roots need time to breathe between mist cycles.
- Check for clogged or dripping nozzles that keep roots constantly wet.

### More_Light
- Plants are leggy and stretched. Stems are thin and reaching toward the light. Leaves are pale green or smaller than normal.
- Lower leaves may yellow and drop because they are shaded out.
- This means the grow lights need to be on longer, positioned closer, or are not bright enough.
- Extend the light schedule or check that the lights are functioning properly.

### Less_Light
- Leaf edges burn or bleach. Upper leaves may yellow while veins stay green. Leaves curl upward or become crispy.
- Light burn affects the top of the plant first, closest to the light source.
- This is different from nitrogen deficiency, which starts at the bottom.
- Reduce light hours or increase the distance between lights and plants.

### Nutrient_Burn
- Leaf tips and margins turn brown and crispy. A yellow halo often separates the burned edge from healthy green tissue.
- This happens when nutrient concentration is too high in the misting solution.
- In aeroponics, salt buildup on roots or nozzles can concentrate nutrients beyond safe levels.
- Flush the system with clean water. Reduce nutrient concentration in the solution.
- Check EC/TDS levels if the user has a meter. For leafy greens, EC should be around 1.0-1.6 mS/cm.

### Pathogen
- This is the most urgent class. It means the model detected signs of disease or infection.
- Symptoms vary: powdery white coating (mildew), black or brown mushy spots (fungal rot), unusual lesions or patterns on leaves.
- Isolate affected plants immediately if possible to prevent spread.
- Improve air circulation. Stagnant, humid air is the number one enabler of fungal disease.
- Remove severely affected leaves or plants. Do not compost them.
- This class warrants immediate attention and follow-up monitoring.

## Vision Detection Classes in Detail

### Chlorosis (yellowing)
- Yellow leaves or yellow patches where green should be.
- Causes: nutrient deficiency (nitrogen, iron, magnesium, or manganese), overwatering and root damage, pH imbalance locking out nutrients, or root rot restricting nutrient uptake.
- If yellowing starts at the bottom of the plant and moves up, suspect nitrogen deficiency.
- If yellowing is between the veins while veins stay green (interveinal chlorosis), suspect iron or magnesium deficiency.
- If yellowing is uniform across the plant, suspect overwatering or root problems.
- Check the environment log for recent overwatering patterns and the water level trend.

### Necrosis (dead tissue)
- Brown or black dead patches on leaves. Tissue is dry and papery, or dark and mushy.
- Causes: severe nutrient burn, disease infection, extreme temperature stress, chemical damage, or prolonged drought.
- Dry, crispy brown patches often point to fertilizer burn or low humidity.
- Dark, mushy patches suggest fungal or bacterial infection.
- Necrosis at leaf margins (edges) often indicates potassium deficiency or salt burn.
- Necrosis is permanent — the dead tissue will not recover. Focus on preventing spread and treating the cause.

### Pest
- Visible insect damage: holes in leaves, stippling (tiny dots), webbing, sticky residue, or distorted new growth.
- Common indoor pests: aphids (small soft-bodied insects on undersides of leaves and stems), spider mites (tiny dots with fine webbing, thrive in hot dry conditions), fungus gnats (small flies near the base, larvae damage roots), whiteflies (tiny white insects that fly up when disturbed), thrips (slender insects that leave silver streaks on leaves).
- Spider mites are more common in low humidity. Increasing humidity helps prevent them.
- Aphids cluster on new growth and the undersides of leaves. They secrete sticky honeydew.
- Inspect both sides of leaves carefully. Many pests hide on the underside.

### Tip Burn (brown leaf tips)
- Brown, dry, crispy tips on leaves. Starts at the very tip and can progress along the edges.
- Causes: nutrient burn (too much fertilizer), low humidity (tips dry out faster than the rest of the leaf), calcium deficiency (common in fast-growing leafy greens), inconsistent watering, or high EC in the nutrient solution.
- Tip burn is extremely common in hydroponic and aeroponic lettuce. It is often caused by calcium not reaching the leaf tips fast enough during rapid growth.
- Improving air circulation around the canopy helps calcium transport to leaf edges.
- If humidity is below 40%, raising it can reduce tip burn.

### Wilting (drooping leaves)
- Leaves and stems droop, lose rigidity, and hang limply.
- Causes: underwatering (most common), heat stress, root damage or root rot, and sometimes overwatering (roots are damaged and can no longer take up water even though water is present).
- If the reservoir is full and plants are still wilting, suspect root rot or heat stress rather than drought.
- Check root health. Healthy aeroponic roots are white, fluffy, and fine. Brown, slimy, or mushy roots indicate rot.
- Wilting in the afternoon under lights that recovers overnight often means the plant is transpiring faster than it can absorb water. Increase misting frequency.
- Sudden wilting of the entire plant is more alarming than gradual drooping of lower leaves.

## Common Nutrient Deficiencies

- Nitrogen: older (lower) leaves yellow first, then the whole plant turns pale green. Growth slows. Most common deficiency.
- Phosphorus: leaves and stems turn dark green or purple. Growth is stunted. Affects older leaves first.
- Potassium: leaf edges yellow and brown, starting from the tips. Older leaves affected first. Edges look scorched.
- Calcium: new growth is distorted, curled, or stunted. Tip burn on young leaves. Blossom end rot in fruiting plants.
- Magnesium: interveinal chlorosis on older leaves — yellowing between veins while veins stay green. Leaves may develop a mottled appearance.
- Iron: interveinal chlorosis on new (upper) leaves. In severe cases, entire young leaves turn white or pale yellow. Veins remain distinctly green.

## General Aeroponic Care Tips

- Root zone oxygen is critical. Aeroponic roots are exposed to air by design. If they stay too wet, oxygen is displaced and roots suffocate. This is the most common cause of root rot in aeroponics.
- Healthy aeroponic roots are bright white, fluffy, and covered in fine root hairs. Dark, brown, or slimy roots are a problem.
- Air circulation matters as much as water and light. Stagnant air promotes mold, mildew, and uneven temperature/humidity. A small fan can make a big difference.
- Misting intervals are a balancing act. The goal is to mist just before the previous cycle has dried. Typical starting points are 3 seconds on, 3 minutes off, but this varies with plant size, temperature, and humidity.
- Water temperature in the reservoir should stay between 60-72°F. Warmer water holds less dissolved oxygen and encourages pathogen growth. Cooler water slows nutrient uptake.
- When diagnosing problems, always check multiple data sources. A single reading can be misleading. Look at sensor trends over hours or days, not just the current snapshot.
- After any major change (transplanting, adjusting lights, changing nutrient concentration), give the plants 3-7 days to respond before making another change. Plants are slow to show improvement.
- Prevention is always easier than treatment. Maintaining stable conditions is more important than hitting perfect numbers.
