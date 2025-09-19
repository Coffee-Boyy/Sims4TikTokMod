// Default gift mappings - Enhanced with dopamine-inducing Sims 4 interactions for livestream mod
export const DEFAULT_GIFT_MAPPINGS = {
    // BASIC GIFTS (1-10 diamonds) - Simple but heartwarming interactions
    'rose': 'romantic_hug', // Classic romantic gesture - sim gives a tender hug with rose petals effect
    'music_on_stage': 'dance_together', // Sim breaks into spontaneous dance with musical notes VFX
    'gg': 'victory_celebration', // Sim does a victory dance with "GG" text bubble and confetti
    'youre_awesome': 'friendly_compliment', // Sim gives enthusiastic compliment with sparkle effects
    'tiktok': 'dance_together', // TikTok dance trend with trending music and effects
    'love_you_so_much': 'flirty_compliment', // Sim blows kiss with heart emoji bubble and pink sparkles
    'ice_cream_cone': 'give_gift', // Sim offers ice cream with happy moodlet and cooling VFX
    'heart_me': 'blow_kiss', // Sim blows kiss with floating hearts and romantic music
    'thumbs_up': 'friendly_compliment', // Sim gives thumbs up with approval sparkles
    'heart': 'blow_kiss', // Simple heart gesture with floating heart particles
    'cake_slice': 'give_gift', // Sim shares cake with birthday party effects and candles
    'glow_stick': 'show_off', // Sim waves glow stick with neon trail effects and party music
    'love_you': 'flirty_compliment', // Sweet love declaration with floating hearts
    'team_bracelet': 'friendly_hug', // Team spirit hug with friendship bracelet VFX
    'finger_heart': 'wink', // Cute finger heart gesture with sparkle effects
    'popcorn': 'tell_joke', // Sim tells joke while eating popcorn with laughter bubbles
    'cheer_you_up': 'high_five', // Encouraging high-five with motivational sparkles
    'rosa': 'romantic_hug', // Elegant rose-themed romantic embrace with petals
    
    // PREMIUM GIFTS (20-500 diamonds) - More exciting interactions with VFX
    'perfume': 'flirty_compliment', // Sim applies perfume with scent cloud VFX and flirty wink
    'doughnut': 'give_gift', // Sim shares donut with sugar sparkles and happy eating animation
    'paper_crane': 'create_cat_sim', // Magical paper crane transforms into a beautiful cat companion
    'little_crown': 'royal_introduction', // Sim wears crown and does royal wave with golden sparkles
    'game_controller': 'gaming_session', // Sim plays video game with controller with gaming VFX
    'confetti': 'celebration_dance', // Sim does celebration dance with colorful confetti explosion
    'heart_rain': 'romantic_kiss', // Passionate kiss under falling hearts with romantic lighting
    'love_you_premium': 'passionate_kiss', // Deep romantic kiss with heart explosion effects
    'sunglasses': 'cool_pose', // Sim strikes cool pose with sunglasses and attitude sparkles
    'sparklers': 'firework_show', // Sim waves sparklers with bright trail effects and crackling sounds
    'corgi': 'create_small_dog_sim', // Adorable corgi appears with wagging tail and happy barks
    'boxing_gloves': 'power_pose', // Sim does boxing pose with power aura and strength effects
    'money_gun': 'money_rain', // Sim shoots money gun with cash rain VFX and cha-ching sounds
    'vr_goggles': 'virtual_reality', // Sim puts on VR goggles with digital world effects
    
    // LUXURY GIFTS (700-5000 diamonds) - Spectacular interactions with major VFX
    'swan': 'elegant_dance', // Graceful swan-like dance with water effects and elegance sparkles
    'train': 'adventure_selfie', // Sim takes epic selfie on train with motion blur and adventure music
    'galaxy': 'cosmic_transformation', // Sim transforms with galaxy effects, stars, and cosmic energy
    'silver_sports_car': 'speed_demon', // Sim poses with sports car with speed lines and engine revving
    'fireworks': 'firework_celebration', // Massive firework display with sim celebrating underneath
    'chasing_dream': 'dream_sequence', // Sim enters dream-like state with floating elements and ethereal effects
    'gift_box': 'mystery_gift', // Sim opens giant gift box with surprise explosion and rainbow effects
    'baby_dragon': 'dragon_companion', // Baby dragon appears with fire breath and magical bonding
    'motorcycle': 'biker_pose', // Sim strikes biker pose with motorcycle and wind effects
    'private_jet': 'jet_setter', // Sim boards private jet with luxury travel effects and champagne
    
    // EXCLUSIVE GIFTS (7000+ diamonds) - Ultimate dopamine-inducing experiences
    'sports_car': 'supercar_showcase', // Epic supercar reveal with dramatic lighting and crowd cheers
    'luxury_yacht': 'yacht_party', // Sim hosts yacht party with ocean effects and luxury celebration
    'interstellar': 'space_journey', // Sim travels through space with cosmic effects and alien encounters
    'crystal_heart': 'eternal_bond', // Magical crystal heart creates eternal bond with mystical effects
    'tiktok_shuttle': 'space_mission', // Sim embarks on space mission with rocket effects and zero gravity
    'phoenix': 'rebirth_ceremony', // Sim undergoes phoenix rebirth with fire and rebirth effects
    'lion': 'royal_coronation', // Sim becomes royalty with crown ceremony and royal fanfare
    'tiktok_universe': 'universe_creation', // Sim creates their own universe with cosmic creation effects
};

export const SIMS_INTERACTIONS = [
    // Basic Interactions
    { value: 'none', label: 'No Interaction', icon: '🚫' },
    { value: 'friendly_hug', label: 'Friendly Hug', icon: '🤗' },
    { value: 'romantic_hug', label: 'Romantic Hug', icon: '💕' },
    { value: 'friendly_compliment', label: 'Friendly Compliment', icon: '😊' },
    { value: 'flirty_compliment', label: 'Flirty Compliment', icon: '😘' },
    { value: 'blow_kiss', label: 'Blow Kiss', icon: '😘' },
    { value: 'wink', label: 'Wink Playfully', icon: '😉' },
    { value: 'high_five', label: 'High Five', icon: '🙌' },
    { value: 'give_gift', label: 'Give Gift', icon: '🎁' },
    { value: 'tell_joke', label: 'Tell Joke', icon: '😂' },
    { value: 'dance_together', label: 'Dance Together', icon: '💃' },
    { value: 'show_off', label: 'Show Off', icon: '✨' },
    
    // Enhanced Basic Interactions
    { value: 'victory_celebration', label: 'Victory Celebration', icon: '🏆' },
    { value: 'romantic_kiss', label: 'Romantic Kiss', icon: '💋' },
    { value: 'passionate_kiss', label: 'Passionate Kiss', icon: '😍' },
    { value: 'royal_introduction', label: 'Royal Introduction', icon: '👑' },
    { value: 'gaming_session', label: 'Gaming Session', icon: '🎮' },
    { value: 'celebration_dance', label: 'Celebration Dance', icon: '🎉' },
    { value: 'cool_pose', label: 'Cool Pose', icon: '😎' },
    { value: 'firework_show', label: 'Firework Show', icon: '🎆' },
    { value: 'power_pose', label: 'Power Pose', icon: '💪' },
    { value: 'money_rain', label: 'Money Rain', icon: '💰' },
    { value: 'virtual_reality', label: 'Virtual Reality', icon: '🥽' },
    
    // Luxury Interactions
    { value: 'elegant_dance', label: 'Elegant Dance', icon: '🦢' },
    { value: 'adventure_selfie', label: 'Adventure Selfie', icon: '📸' },
    { value: 'cosmic_transformation', label: 'Cosmic Transformation', icon: '🌌' },
    { value: 'speed_demon', label: 'Speed Demon', icon: '🏎️' },
    { value: 'firework_celebration', label: 'Firework Celebration', icon: '🎇' },
    { value: 'dream_sequence', label: 'Dream Sequence', icon: '💭' },
    { value: 'mystery_gift', label: 'Mystery Gift', icon: '🎁' },
    { value: 'dragon_companion', label: 'Dragon Companion', icon: '🐉' },
    { value: 'biker_pose', label: 'Biker Pose', icon: '🏍️' },
    { value: 'jet_setter', label: 'Jet Setter', icon: '✈️' },
    
    // Exclusive Interactions
    { value: 'supercar_showcase', label: 'Supercar Showcase', icon: '🏎️' },
    { value: 'yacht_party', label: 'Yacht Party', icon: '🛥️' },
    { value: 'space_journey', label: 'Space Journey', icon: '🚀' },
    { value: 'eternal_bond', label: 'Eternal Bond', icon: '💎' },
    { value: 'space_mission', label: 'Space Mission', icon: '🛸' },
    { value: 'rebirth_ceremony', label: 'Rebirth Ceremony', icon: '🔥' },
    { value: 'royal_coronation', label: 'Royal Coronation', icon: '👑' },
    { value: 'universe_creation', label: 'Universe Creation', icon: '🌌' },
    
    // Pet Creation Interactions
    { value: 'create_sim', label: 'Create a Sim', icon: '🧑‍🎨' },
    { value: 'create_small_dog_sim', label: 'Create a Small Dog', icon: '🐶' },
    { value: 'create_large_dog_sim', label: 'Create a Large Dog', icon: '🐶' },
    { value: 'create_cat_sim', label: 'Create a Cat', icon: '🐱' },
    
    // Special Interactions
    { value: 'take_selfie', label: 'Take Selfie Together', icon: '📸' },
    { value: 'playful_poke', label: 'Playful Poke', icon: '👉' },
    { value: 'excited_introduction', label: 'Excited Introduction', icon: '🤩' },
    { value: 'confident_introduction', label: 'Confident Introduction', icon: '😎' },
    { value: 'woohoo', label: 'WooHoo', icon: '🔥' },
    { value: 'propose', label: 'Propose Marriage', icon: '💍' }
];

// Gift Configuration Data - Updated from streamtoearn.io/gifts with actual icon URLs
export const TIKTOK_GIFTS = [
    // Basic Gifts (1-10 diamonds)
    { name: 'Rose', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/eba3a9bb85c33e017f3648eaf88d7189~tplv-obj.webp', cost: 1, tier: 'basic', id: 'rose' },
    { name: 'Music on Stage', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/d2a59d961490de4c72fed3690e44d1ec.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'music_on_stage' },
    { name: 'GG', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/3f02fa9594bd1495ff4e8aa5ae265eef~tplv-obj.webp', cost: 1, tier: 'basic', id: 'gg' },
    { name: 'You\'re awesome', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/e9cafce8279220ed26016a71076d6a8a.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'youre_awesome' },
    { name: 'TikTok', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/802a21ae29f9fae5abe3693de9f874bd~tplv-obj.webp', cost: 1, tier: 'basic', id: 'tiktok' },
    { name: 'Love you so much', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/fc549cf1bc61f9c8a1c97ebab68dced7.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'love_you_so_much' },
    { name: 'Ice Cream Cone', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/968820bc85e274713c795a6aef3f7c67~tplv-obj.webp', cost: 1, tier: 'basic', id: 'ice_cream_cone' },
    { name: 'Heart Me', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/d56945782445b0b8c8658ed44f894c7b~tplv-obj.webp', cost: 1, tier: 'basic', id: 'heart_me' },
    { name: 'Thumbs Up', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/570a663e27bdc460e05556fd1596771a~tplv-obj.webp', cost: 1, tier: 'basic', id: 'thumbs_up' },
    { name: 'Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/dd300fd35a757d751301fba862a258f1~tplv-obj.webp', cost: 1, tier: 'basic', id: 'heart' },
    { name: 'Cake Slice', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/f681afb4be36d8a321eac741d387f1e2~tplv-obj.webp', cost: 1, tier: 'basic', id: 'cake_slice' },
    { name: 'Glow Stick', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8e1a5d66370c5586545e358e37c10d25~tplv-obj.webp', cost: 1, tier: 'basic', id: 'glow_stick' },
    { name: 'Love you', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/ab0a7b44bfc140923bb74164f6f880ab~tplv-obj.webp', cost: 1, tier: 'basic', id: 'love_you' },
    { name: 'Team Bracelet', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/54cb1eeca369e5bea1b97707ca05d189.png~tplv-obj.webp', cost: 2, tier: 'basic', id: 'team_bracelet' },
    { name: 'Finger Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/a4c4dc437fd3a6632aba149769491f49.png~tplv-obj.webp', cost: 5, tier: 'basic', id: 'finger_heart' },
    { name: 'Popcorn', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/676d2d4c31a8979f1fd06cdf5ecd922f~tplv-obj.webp', cost: 5, tier: 'basic', id: 'popcorn' },
    { name: 'Cheer You Up', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/97e0529ab9e5cbb60d95fc9ff1133ea6~tplv-obj.webp', cost: 9, tier: 'basic', id: 'cheer_you_up' },
    { name: 'Rosa', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/eb77ead5c3abb6da6034d3cf6cfeb438~tplv-obj.webp', cost: 10, tier: 'basic', id: 'rosa' },
    
    // Premium Gifts (20-500 diamonds)
    { name: 'Perfume', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/20b8f61246c7b6032777bb81bf4ee055~tplv-obj.webp', cost: 20, tier: 'premium', id: 'perfume' },
    { name: 'Doughnut', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4e7ad6bdf0a1d860c538f38026d4e812~tplv-obj.webp', cost: 30, tier: 'premium', id: 'doughnut' },
    { name: 'Paper Crane', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/0f158a08f7886189cdabf496e8a07c21~tplv-obj.webp', cost: 99, tier: 'premium', id: 'paper_crane' },
    { name: 'Little Crown', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/cf3db11b94a975417043b53401d0afe1~tplv-obj.webp', cost: 99, tier: 'premium', id: 'little_crown' },
    { name: 'Game Controller', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/20ec0eb50d82c2c445cb8391fd9fe6e2~tplv-obj.webp', cost: 100, tier: 'premium', id: 'game_controller' },
    { name: 'Confetti', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/cb4e11b3834e149f08e1cdcc93870b26~tplv-obj.webp', cost: 100, tier: 'premium', id: 'confetti' },
    { name: 'Heart Rain', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/be28619d8b8d1dc03f91c7c63e4e0260.png~tplv-obj.webp', cost: 149, tier: 'premium', id: 'heart_rain' },
    { name: 'Love You', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/134e51c00f46e01976399883ca4e4798~tplv-obj.webp', cost: 199, tier: 'premium', id: 'love_you_premium' },
    { name: 'Sunglasses', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/08af67ab13a8053269bf539fd27f3873.png~tplv-obj.webp', cost: 199, tier: 'premium', id: 'sunglasses' },
    { name: 'Sparklers', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/192a873e366e2410da4fa406aba0e0af.png~tplv-obj.webp', cost: 199, tier: 'premium', id: 'sparklers' },
    { name: 'Corgi', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/148eef0884fdb12058d1c6897d1e02b9~tplv-obj.webp', cost: 299, tier: 'premium', id: 'corgi' },
    { name: 'Boxing Gloves', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9f8bd92363c400c284179f6719b6ba9c~tplv-obj.webp', cost: 299, tier: 'premium', id: 'boxing_gloves' },
    { name: 'Money Gun', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/e0589e95a2b41970f0f30f6202f5fce6~tplv-obj.webp', cost: 500, tier: 'premium', id: 'money_gun' },
    { name: 'VR Goggles', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/18c51791197b413bbd1b4f1b983bda36.png~tplv-obj.webp', cost: 500, tier: 'premium', id: 'vr_goggles' },
    
    // Luxury Gifts (700-5000 diamonds)
    { name: 'Swan', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/97a26919dbf6afe262c97e22a83f4bf1~tplv-obj.webp', cost: 699, tier: 'luxury', id: 'swan' },
    { name: 'Train', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4227ed71f2c494b554f9cbe2147d4899~tplv-obj.webp', cost: 899, tier: 'luxury', id: 'train' },
    { name: 'Galaxy', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/79a02148079526539f7599150da9fd28.png~tplv-obj.webp', cost: 1000, tier: 'luxury', id: 'galaxy' },
    { name: 'Silver Sports Car', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/f9d784269da31a71e58b10de6fc34cde.png~tplv-obj.webp', cost: 1000, tier: 'luxury', id: 'silver_sports_car' },
    { name: 'Fireworks', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9494c8a0bc5c03521ef65368e59cc2b8~tplv-obj.webp', cost: 1088, tier: 'luxury', id: 'fireworks' },
    { name: 'Chasing the Dream', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/1ea8dbb805466c4ced19f29e9590040f~tplv-obj.webp', cost: 1500, tier: 'luxury', id: 'chasing_dream' },
    { name: 'Gift Box', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9cc22f7c8ac233e129dec7b981b91b76~tplv-obj.webp', cost: 1999, tier: 'luxury', id: 'gift_box' },
    { name: 'Baby Dragon', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/733030ca95fe6f757533aec40bf2af3a.png~tplv-obj.webp', cost: 2000, tier: 'luxury', id: 'baby_dragon' },
    { name: 'Motorcycle', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/6517b8f2f76dc75ff0f4f73107f8780e~tplv-obj.webp', cost: 2988, tier: 'luxury', id: 'motorcycle' },
    { name: 'Private Jet', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/921c6084acaa2339792052058cbd3fd3~tplv-obj.webp', cost: 4888, tier: 'luxury', id: 'private_jet' },
    
    // Exclusive Gifts (7000+ diamonds)
    { name: 'Sports Car', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/e7ce188da898772f18aaffe49a7bd7db~tplv-obj.webp', cost: 7000, tier: 'exclusive', id: 'sports_car' },
    { name: 'Luxury Yacht', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/a97ef636c4e0494b2317c58c9edba0a8.png~tplv-obj.webp', cost: 10000, tier: 'exclusive', id: 'luxury_yacht' },
    { name: 'Interstellar', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8520d47b59c202a4534c1560a355ae06~tplv-obj.webp', cost: 10000, tier: 'exclusive', id: 'interstellar' },
    { name: 'Crystal Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/08095e18ae3da6ad5dcf23ce68eb1483.png~tplv-obj.webp', cost: 14999, tier: 'exclusive', id: 'crystal_heart' },
    { name: 'TikTok Shuttle', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8ef48feba8dd293a75ae9d4376fb17c9~tplv-obj.webp', cost: 20000, tier: 'exclusive', id: 'tiktok_shuttle' },
    { name: 'Phoenix', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/ef248375c4167d70c1642731c732c982~tplv-obj.webp', cost: 25999, tier: 'exclusive', id: 'phoenix' },
    { name: 'Lion', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4fb89af2082a290b37d704e20f4fe729~tplv-obj.webp', cost: 29999, tier: 'exclusive', id: 'lion' },
    { name: 'TikTok Universe', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8f471afbcebfda3841a6cc515e381f58~tplv-obj.webp', cost: 44999, tier: 'exclusive', id: 'tiktok_universe' }
];
