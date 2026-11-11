/* Kalpa Jyotish curated names, written for Kalpa Labs (not copied from any list).
   Each row: English spelling | Hindi (Devanagari) | gender (m, f, u = any) | meaning | optional Telugu override.
   Telugu spelling is otherwise converted from the Devanagari by Jyotish.devToTelugu. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.JyotishNames = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const ROWS = `
Chetan|चेतन|m|awareness
Chaitanya|चैतन्य|m|consciousness, life
Chaitra|चैत्रा|f|born in the first spring month
Lakshmi|लक्ष्मी|f|goddess of wealth and grace
Lalitha|ललिता|f|graceful, playful
Lavanya|लावण्या|f|beauty, charm
Lakshman|लक्ष्मण|m|brother of Rama, fortunate
Lasya|लास्या|f|graceful dance
Leela|लीला|f|divine play
Lekha|लेखा|f|writing, line
Lochan|लोचन|m|eye
Lokesh|लोकेश|m|lord of the world
Lohith|लोहित|m|red, bright
Aarav|आरव|m|calm, peaceful
Ananya|अनन्या|f|one of a kind
Arjun|अर्जुन|m|bright, the Pandava archer
Aditi|अदिति|f|boundless, mother of the gods
Akhil|अखिल|m|whole, complete
Anil|अनिल|m|wind
Abhinav|अभिनव|m|new, fresh
Aditya|आदित्य|m|the sun
Amrutha|अमृता|f|nectar, immortal
Anjali|अंजलि|f|offering with folded hands
Anvitha|अन्विता|f|connected, understood
Aryan|आर्यन|m|noble
Aishwarya|ऐश्वर्या|f|prosperity
Ishaan|ईशान|m|lord of the north east
Indu|इंदु|f|the moon
Ishita|इशिता|f|desired, mastery
Eshwar|ईश्वर|m|the supreme lord
Uma|उमा|f|goddess Parvati
Uday|उदय|m|rising, dawn
Ujwal|उज्ज्वल|m|bright, shining
Usha|उषा|f|dawn
Ekta|एकता|f|unity
Ekansh|एकांश|m|a whole part
Om|ओम|m|the sacred sound
Ojas|ओजस|m|vitality, inner light
Varun|वरुण|m|lord of the waters
Vasudha|वसुधा|f|the earth
Vamsi|वंशी|m|flute
Varsha|वर्षा|f|rain
Vikram|विक्रम|m|valour
Vidya|विद्या|f|knowledge
Vijay|विजय|m|victory
Vinay|विनय|m|humility
Vihaan|विहान|m|dawn
Vedant|वेदांत|m|essence of the Vedas
Venkatesh|वेंकटेश|m|lord of Venkata hill|వెంకటేశ్
Vennela|वेन्नेला|f|moonlight (Telugu)|వెన్నెల
Vaishnavi|वैष्णवी|f|devotee of Vishnu
Kavya|काव्या|f|poetry
Karthik|कार्तिक|m|son of Shiva, a holy month
Kalyani|कल्याणी|f|auspicious
Kamala|कमला|f|lotus
Kavitha|कविता|f|poem
Kalyan|कल्याण|m|welfare, blessing
Kiran|किरण|u|ray of light
Keerthi|कीर्ति|f|fame, glory
Kishore|किशोर|m|youth
Krishna|कृष्ण|m|dark one, Lord Krishna
Kumar|कुमार|m|prince
Kusuma|कुसुमा|f|flower
Ghanashyam|घनश्याम|m|dark as a rain cloud
Chhaya|छाया|f|shade, shelter
Kedar|केदार|m|lord of Kedarnath
Ketaki|केतकी|f|a fragrant flower
Keshav|केशव|m|Lord Krishna
Komal|कोमल|f|soft, tender
Kousalya|कौसल्या|f|mother of Rama
Harsha|हर्ष|m|joy
Hamsa|हंसा|f|swan
Hari|हरि|m|Lord Vishnu
Harika|हारिका|f|one who wins hearts
Hasini|हासिनी|f|smiling
Himani|हिमानी|f|snow
Hitesh|हितेश|m|lord of goodness
Hema|हेमा|f|gold
Hemant|हेमंत|m|early winter
Madhav|माधव|m|Lord Krishna
Mahesh|महेश|m|Lord Shiva
Manasa|मानसा|f|of the mind
Malini|मालिनी|f|garland maker
Madhuri|माधुरी|f|sweetness
Mahathi|महती|f|great; Narada's veena
Manoj|मनोज|m|born of the mind
Mihir|मिहिर|m|the sun
Mitra|मित्र|m|friend
Meera|मीरा|f|devotee of Krishna
Mukund|मुकुंद|m|giver of freedom
Mukta|मुक्ता|f|pearl
Meghana|मेघना|f|cloud
Megha|मेघा|f|cloud
Mohan|मोहन|m|charming
Mounika|मौनिका|f|silent one
Mokshagna|मोक्षज्ञ|m|one who knows liberation
Pavan|पवन|m|wind
Padma|पद्मा|f|lotus
Parvati|पार्वती|f|daughter of the mountain
Prakash|प्रकाश|m|light
Pranav|प्रणव|m|the sacred Om
Pallavi|पल्लवी|f|new leaves
Pranathi|प्रणति|f|prayer, salutation
Priya|प्रिया|f|beloved
Preethi|प्रीति|f|love
Pushpa|पुष्पा|f|flower
Puneeth|पुनीत|m|pure
Purnima|पूर्णिमा|f|full moon
Pooja|पूजा|f|worship
Pournami|पौर्णमी|f|full moon (Telugu)|పౌర్ణమి
Toshan|तोषण|m|contentment
Shankar|शंकर|m|Lord Shiva
Sharada|शारदा|f|goddess Saraswati
Shanti|शांति|f|peace
Sravan|श्रवण|m|listening; a nakshatra
Sravani|श्रावणी|f|born in Shravana month
Srikanth|श्रीकांत|m|beloved of Lakshmi
Srinivas|श्रीनिवास|m|abode of Lakshmi
Siva|शिव|m|auspicious, Lord Shiva
Ram|राम|m|Lord Rama
Radha|राधा|f|beloved of Krishna
Raghav|राघव|m|Lord Rama
Rajesh|राजेश|m|king of kings
Ramya|रम्या|f|pleasing
Rakesh|राकेश|m|lord of the full moon night
Ramesh|रमेश|m|Lord Vishnu
Raju|राजू|m|king
Rishi|ऋषि|m|sage
Rithika|ऋतिका|f|movement, stream
Rishabh|ऋषभ|m|excellent
Rukmini|रुक्मिणी|f|wife of Krishna
Rudra|रुद्र|m|Lord Shiva
Ruchi|रुचि|f|taste, interest
Revathi|रेवती|f|a nakshatra, prosperity
Renu|रेणु|f|grain of sand, pollen
Rohan|रोहन|m|ascending
Rohit|रोहित|m|red, the rising sun
Roshni|रोशनी|f|light
Tanvi|तन्वी|f|delicate
Tarun|तरुण|m|young
Tara|तारा|f|star
Tanuja|तनुजा|f|daughter
Tilak|तिलक|m|mark of honour
Tulasi|तुलसी|f|holy basil
Tushar|तुषार|m|dew, frost
Tejas|तेजस|m|brilliance
Teja|तेजा|m|radiance
Tejaswini|तेजस्विनी|f|radiant
Navya|नव्या|f|new, young
Naveen|नवीन|m|new
Nandini|नंदिनी|f|daughter, joy
Narayan|नारायण|m|Lord Vishnu
Nikhil|निखिल|m|whole, entire
Nithya|नित्या|f|eternal
Nirmala|निर्मला|f|pure
Nupur|नूपुर|f|anklet
Neha|नेहा|f|love, rain
Netra|नेत्रा|f|eye, guide
Yamini|यामिनी|f|night
Yash|यश|m|fame, success
Yashoda|यशोदा|f|mother of Krishna
Yashwanth|यशवंत|m|famous
Yamuna|यमुना|f|the holy river
Yuvaraj|युवराज|m|crown prince
Yuktha|युक्ता|f|skilled, united
Yogesh|योगेश|m|lord of yoga
Yogitha|योगिता|f|enchanted
Bharat|भरत|m|India; brother of Rama
Bhavana|भावना|f|feeling
Bhargav|भार्गव|m|Lord Shiva
Bhavya|भव्या|f|grand
Bhanu|भानु|m|the sun
Bheema|भीम|m|mighty
Bhuvan|भुवन|m|the world
Bhumika|भूमिका|f|the earth
Dhanush|धनुष|m|bow
Dhanya|धन्या|f|blessed
Dharani|धरणी|f|the earth
Phalguni|फाल्गुनी|f|born in Phalguna month
Janaki|जानकी|f|goddess Sita
Jayant|जयंत|m|victorious
Jaya|जया|f|victory
Jahnavi|जाह्नवी|f|the Ganga
Jitendra|जितेंद्र|m|master of the senses
Jeevan|जीवन|m|life
Juhi|जूही|f|jasmine
Jyothi|ज्योति|f|light
Ganesh|गणेश|m|Lord Ganesha
Gayatri|गायत्री|f|a holy hymn
Gagan|गगन|m|sky
Girish|गिरीश|m|lord of the mountains
Geetha|गीता|f|song; the Gita
Guru|गुरु|m|teacher
Gunjan|गुंजन|u|humming
Gopal|गोपाल|m|protector of cows
Govind|गोविंद|m|Lord Krishna
Gowri|गौरी|f|goddess Parvati
Gautam|गौतम|m|the Buddha's family name
Sai|साई|u|saint, flower
Saritha|सरिता|f|river
Sahana|सहना|f|patience
Sandeep|संदीप|m|lit lamp
Saanvi|सान्वी|f|goddess Lakshmi
Sahithi|साहिती|f|literature
Satya|सत्य|u|truth
Swathi|स्वाति|f|a nakshatra, pearl drop
Seetha|सीता|f|wife of Rama
Siddharth|सिद्धार्थ|m|one who reached the goal
Sindhu|सिंधु|f|river, ocean
Smitha|स्मिता|f|smiling
Suresh|सुरेश|m|lord of the gods
Sunitha|सुनीता|f|well behaved
Surya|सूर्य|m|the sun
Sushma|सुषमा|f|beauty
Sneha|स्नेहा|f|affection
Soumya|सौम्या|f|gentle
Sohan|सोहन|m|handsome
Somesh|सोमेश|m|lord of the moon
Darshan|दर्शन|m|sight, vision
Damini|दामिनी|f|lightning
Daya|दया|f|kindness
Divya|दिव्या|f|divine
Dinesh|दिनेश|m|the sun
Deepak|दीपक|m|lamp
Deepika|दीपिका|f|little lamp
Deekshitha|दीक्षिता|f|initiated
Durga|दुर्गा|f|the invincible goddess
Dushyant|दुष्यंत|m|a king of the Puru line
Dev|देव|m|god
Devika|देविका|f|little goddess
Devendra|देवेंद्र|m|king of the gods
Chandra|चंद्र|m|the moon
Charan|चरण|m|feet of the divine
Chandana|चंदना|f|sandalwood
Charu|चारु|f|beautiful
Charitha|चरिता|f|good conduct
Chinmay|चिन्मय|m|full of awareness
Chitra|चित्रा|f|picture; a nakshatra
Chiranjeevi|चिरंजीवी|m|long lived
`;
  return ROWS.trim().split('\n').map((line) => {
    const [en, hi, g, meaning, te] = line.split('|');
    return { en, hi, g, meaning, te: te || null };
  });
});
