export const rewards = [
    {
        description: "Get 1 click bot",
        apply(clicker) {
            clicker.bots.clickbot.purchased += 1;
            
        },
        maxLevel: 3,
    },
    {
        description: "Get 10 click bot",
        apply(clicker) {
            clicker.bots.clickbot.purchased += 10;
        },
        minLevel: 1,
        maxLevel: 4,
    },
    {
        description: "Increase bot power!",
        apply(clicker){
            clicker.multiplier += 1;
        },
        minLevel: 3,
    },
];