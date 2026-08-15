"""Python port of CombatMath, run against real positions from the
committed transcript. Verifies the algorithm before the Java is trusted."""
import itertools

def resolve(attackers, blockers, assign, life):
    dmg = akill = aval = blost = bval = 0
    for a,(ap,at,an) in enumerate(attackers):
        mine=[blockers[b] for b in range(len(blockers)) if assign[b]==a]
        if not mine:
            dmg += ap; continue
        if sum(p for p,_,_ in mine) >= at:
            akill += 1; aval += ap+at
        left = ap
        for bp,bt,bn in sorted(mine,key=lambda x:x[1]):
            if left >= bt:
                left -= bt; blost += 1; bval += bp+bt
    return dict(dmg=dmg,akill=akill,aval=aval,blost=blost,bval=bval,dead=dmg>=life)

def score(o,total):
    if o['dead']: return -10**9
    return 2*(total-o['dmg']) + 3*o['aval'] - 3*o['bval']

def best(attackers, blockers, life):
    total=sum(p for p,_,_ in attackers)
    bestA=None;bestS=-10**18;bestO=None
    for assign in itertools.product(range(-1,len(attackers)), repeat=len(blockers)):
        o=resolve(attackers,blockers,assign,life); s=score(o,total)
        if s>bestS: bestS,bestA,bestO=s,assign,o
    return bestA,bestS,bestO,total

def show(tag, attackers, blockers, life, actual):
    total=sum(p for p,_,_ in attackers)
    ao=resolve(attackers,blockers,actual,life); asc=score(ao,total)
    ba,bs,bo,_=best(attackers,blockers,life)
    print("== %s  life=%d  incoming=%d" % (tag,life,total))
    print("   agent : dmg=%d killed=%d lost=%d dead=%s  score=%d"
          %(ao['dmg'],ao['akill'],ao['blost'],ao['dead'],asc))
    print("   best  : dmg=%d killed=%d lost=%d dead=%s  score=%d"
          %(bo['dmg'],bo['akill'],bo['blost'],bo['dead'],bs))
    print("   assignment best =",ba)
    print("   ALL assignments lethal?" ,
          all(resolve(attackers,blockers,x,life)['dead']
              for x in itertools.product(range(-1,len(attackers)),repeat=len(blockers))))
    print()

# t26: agent at 2 life, blocked ALL FOUR on Shu Elite Infantry
A26=[(2,2,"Glory Seeker"),(3,2,"Knight of the Keep"),(2,3,"Regal Unicorn"),
     (3,3,"Shu Elite Infantry"),(2,2,"Silvercoat Lion")]
B26=[(3,1,"Dromoka Warrior"),(2,4,"Foot Soldiers"),(2,4,"Foot Soldiers"),(2,4,"Foot Soldiers")]
show("t26", A26, B26, 2, (3,3,3,3))

# t20: agent at 20, put all three blockers on the 2/4, let the 3/3 through
A20=[(2,4,"Foot Soldiers"),(3,3,"Shu Elite Infantry")]
B20=[(2,4,"Foot Soldiers"),(2,4,"Foot Soldiers"),(2,2,"Glory Seeker")]
show("t20", A20, B20, 20, (0,0,0))
