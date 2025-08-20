import { Reactive } from "@web/core/utils/reactive";
import { EventBus } from "@odoo/owl";
import { rewards } from "./click_rewards";
import { choose } from "./utils";

export class ClickerModel extends Reactive {
    constructor() {
        super();
        this.clicks = 0;
        this.level = 0;
        this.bus = new EventBus();
        this.bots = {
            clickbot: {
                price: 10,
                level: 0,
                increment: 10,
                purchased: 0,
            },
            bigbot: {
                price: 50,
                level: 1,
                increment: 100,
                purchased: 0,
            }
        };
        this.trees = {
            pearTree: {
                price: 1000,
                level: 4,
                produce: "pear",
                purchased: 0,
            },
            cherryTree: {
                price: 1000,
                level: 4,
                produce: "cherry",
                purchased: 0,
            },
        }
        this.fruits = {
            pear: 0,
            cherry: 0,
        },
        this.multiplier = 1
        this.ticks = 0;
    }

    addClick() {
        this.increment(1);
    }

    tick() {
        this.ticks++;
        for (const bot in this.bots) {
            this.clicks += this.bots[bot].increment * this.bots[bot].purchased * this.multiplier;
        }
        if (this.ticks % 3 === 0) {
            for (const tree in this.trees) {
                this.fruits[this.trees[tree].produce] += this.trees[tree].purchased;
            }
        }
    }

    buyMultiplier() {
        if (this.clicks < 100) {
            return false;
        }
        this.clicks -= 100;
        this.multiplier++;
    }

    increment(inc) {
        this.clicks += inc;
        if (this.milestones[this.level] && this.clicks >= this.milestones[this.level].clicks) 
            {
                this.bus.trigger("MILESTONE", this.milestones[this.level]);
                this.level += 1;
            }
    }

    buyBot(name) {
        if (!Object.keys(this.bots).includes(name)) {
            throw new Error(`Invalid bot name ${name}`);
        }
        if (this.clicks < this.bots[name].price) {
            return false;
        }
        this.clicks -= this.bots[name].price;
        this.bots[name].purchased += 1;
    }

    giveReward() {
        const availableReward = [];
        for (const reward of rewards) {
            if (reward.minLevel <= this.level || !reward.minLevel) {
                if (reward.maxLevel >= this.level || !reward.maxLevel) {
                    availableReward.push(reward);
                }
            }
        }
        const reward = choose(availableReward);
        this.bus.trigger("REWARD", reward);
        return choose(availableReward);
    }
    
    buyTree(name) {
        if (!Object.keys(this.trees).includes(name)) {
            throw new Error(`Invalid tree name ${name}`);
        }
        if (this.clicks < this.trees[name].price) {
            return false;
        }
        this.clicks -= this.trees[name].price;
        this.trees[name].purchased += 1;
    }


    get milestones() {
            return [
                { clicks: 10, unlock: "clickBot" },
                { clicks: 50, unlock: "bigBot" },
                { clicks: 100, unlock: "power multiplier" },
                { clicks: 1000, unlock: "pear tree & cherry tree" },


            ];
        }
    }
