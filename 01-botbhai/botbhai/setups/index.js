// Loads every BotBhai industry setup into the engine. Each setup is sold and deployed separately.
const BotBhai = require("../core/engine.js");
const SETUPS = {
  salon: require("./salon/bot.config.js"),
  realestate: require("./realestate/bot.config.js"),
  gym: require("./gym/bot.config.js"),
  examkits: require("./examkits/bot.config.js"),
};
for (const cfg of Object.values(SETUPS)) BotBhai.register(cfg);
module.exports = { BotBhai, SETUPS };
