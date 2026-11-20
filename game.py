#!/usr/bin/env python3
"""Đảo Đèn Lồng — single-file, dependency-free game and deterministic contract runner."""
import argparse
import json
import math
import random
import sys
from pathlib import Path

HZ = 60
T = {
    "player_speed": 5.0, "carry_capacity": 10, "lantern_cost": 5,
    "lantern_count_night1": 5, "lantern_count_night2": 6, "lantern_count_night3": 7,
    "pickup_radius": 1.2, "interact_radius": 2.0, "pulse_cost": 1, "pulse_radius": 7.0,
    "night1_duration_s": 300, "night2_duration_s": 360, "night3_duration_s": 420,
    "flames": 3, "invuln_s": 2.0, "hit_drop_ratio": 0.5,
    "pulse_stun_s": 2.0, "pulse_push_m": 2.0, "pulse_cooldown_s": 3.0,
    "safe_radius": 3.0, "shade_speed": 2.5, "shade_hit_radius": 1.0,
    "fall_enabled": True,
    "island_radius_m": 40.0, "jump_velocity_m_s": 7.0, "gravity_m_s2": 18.0,
    "lantern_ring_radius_m": 25.0, "initial_mote_count": 40,
    "initial_mote_spawn_radius_m": 36.0, "initial_shade_count": 3,
    "initial_shade_spawn_radius_m": 32.0,
    "dash_speed_m_s": 12.0, "dash_duration_s": 0.2, "dash_cooldown_s": 1.5,
    "glide_fall_speed_m_s": 2.0,
    "lost_wisp_speed_m_s": 2.0, "lost_wisp_radius_m": 2.0, "lost_wisp_push_m_s": 3.0,
    "wind_charm_radius_m": 1.2, "wind_charm_duration_s": 8.0,
    "strong_wind_speed_m_s": 2.5, "bell_tower_radius_m": 3.0,
    "step_height_m": 0.8, "fall_y_m": -8.0,
    "night2_shade_speed": 2.8, "night3_shade_speed": 3.1,
    "night2_lost_wisp_speed_m_s": 2.0, "night3_lost_wisp_speed_m_s": 2.6,
    "score": {"per_mote": 10, "per_lantern": 100, "per_stun": 25, "per_second_left": 1, "per_flame_left": 50},
}
ISLAND_R = T["island_radius_m"]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def default_lanterns():
    count = T["lantern_count_night1"]
    return [{"id": f"L{i+1}", "pos": [round(T["lantern_ring_radius_m"]*math.cos(i*2*math.pi/count), 3), 0.0,
             round(T["lantern_ring_radius_m"]*math.sin(i*2*math.pi/count), 3)], "lit": False, "deposited": 0}
            for i in range(count)]


class Game:
    def __init__(self, seed=1, scenario=None):
        self.rng = random.Random(seed)
        self.tick = 0
        self.state, self.result = "playing", None
        self.initial_time_left = float(T["night1_duration_s"])
        self.score, self.carried, self.flames = 0, 0, T["flames"]
        self.pos, self.vy, self.on_ground = [0.0, 0.0, 0.0], 0.0, True
        self.invuln = self.pulse_cd = 0
        self.motes, self.shades, self.lanterns = [], [], default_lanterns()
        self.events = []
        self.random_motes = self.random_shades = True
        self.mote_serial = self.shade_serial = 0
        self._spawn_initial()
        if scenario:
            self._scenario(scenario)
            # Scenario construction is setup, not a gameplay event.
            self.events.clear()

    def _mote(self, p):
        self.mote_serial += 1
        self.motes.append({"id": f"M{self.mote_serial}", "pos": [float(x) for x in p]})

    def _shade(self, p, ident=None):
        self.shade_serial += 1
        self.shades.append({"id": ident or f"S{self.shade_serial}", "pos": [float(x) for x in p], "state": "chase", "stun": 0})

    def _spawn_initial(self):
        for _ in range(T["initial_mote_count"]):
            a, r = self.rng.random()*2*math.pi, math.sqrt(self.rng.random())*T["initial_mote_spawn_radius_m"]
            self._mote([r*math.cos(a), 0, r*math.sin(a)])
        for i in range(T["initial_shade_count"]):
            a = 2*math.pi*i/T["initial_shade_count"]
            radius=T["initial_shade_spawn_radius_m"]
            self._shade([radius*math.cos(a), 0, radius*math.sin(a)])
            self.event("shade_spawned", {"id": f"S{i+1}"})

    def _scenario(self, sc):
        if not isinstance(sc, dict): raise ValueError("scenario must be a JSON object")
        pl = sc.get("player", {})
        if not isinstance(pl, dict): raise ValueError("player must be an object")
        self.pos = self._vec(pl.get("pos", [0, 0, 0]), "player.pos")
        self.carried = self._integer(pl.get("carried", 0), "player.carried", 0)
        self.flames = self._integer(pl.get("flames", T["flames"]), "player.flames", 0)
        for flag in ("random_motes", "random_shades"):
            if flag in sc and not isinstance(sc[flag], bool): raise ValueError(f"{flag} must be boolean")
        self.random_motes = bool(sc.get("random_motes", True)); self.random_shades = bool(sc.get("random_shades", True))
        if not self.random_motes and "motes" not in sc: self.motes = []
        if not self.random_shades and "shades" not in sc: self.shades = []
        if "motes" in sc:
            if not isinstance(sc["motes"], list): raise ValueError("motes must be an array")
            self.motes = []; self.mote_serial = 0
            for p in sc["motes"]: self._mote(self._vec(p, "mote"))
        if "shades" in sc:
            if not isinstance(sc["shades"], list): raise ValueError("shades must be an array")
            self.shades = []; self.shade_serial = 0
            for s in sc["shades"]:
                if not isinstance(s, dict): raise ValueError("shade must be an object")
                shade_id = str(s["id"]) if "id" in s else f"S{self.shade_serial+1}"
                self._shade(self._vec(s.get("pos", [0,0,0]), "shade.pos"), shade_id)
                self.event("shade_spawned", {"id": shade_id})
        if "lanterns" in sc:
            if not isinstance(sc["lanterns"], list): raise ValueError("lanterns must be an array")
            byid = {l["id"]: l for l in self.lanterns}
            for item in sc["lanterns"]:
                if not isinstance(item, dict) or item.get("id") not in byid: raise ValueError(f"lantern id must be L1…L{T['lantern_count_night1']}")
                l = byid[item["id"]]
                if "pos" in item: l["pos"] = self._vec(item["pos"], "lantern.pos")
                if "deposited" in item: l["deposited"] = min(T["lantern_cost"], self._integer(item["deposited"], "deposited", 0))
                if "lit" in item and not isinstance(item["lit"], bool): raise ValueError("lantern lit must be boolean")
                l["lit"] = bool(item.get("lit", l["deposited"] >= T["lantern_cost"]))
        if "time_left_s" in sc:
            if isinstance(sc["time_left_s"], bool) or not isinstance(sc["time_left_s"], (int,float)): raise ValueError("time_left_s must be numeric")
            self.initial_time_left = float(sc["time_left_s"])
            if not math.isfinite(self.initial_time_left) or self.initial_time_left < 0: raise ValueError("time_left_s must be nonnegative")
        if self.flames == 0: self.finish("lost", "no_flames")

    @staticmethod
    def _integer(n, name, minimum):
        if isinstance(n, bool) or not isinstance(n, int) or n < minimum: raise ValueError(f"{name} must be an integer >= {minimum}")
        return n

    @staticmethod
    def _vec(p, name):
        if not isinstance(p, list) or len(p) != 3 or any(isinstance(x, bool) or not isinstance(x, (int,float)) or not math.isfinite(x) for x in p):
            raise ValueError(f"{name} must be a finite [x,y,z] array")
        return [float(x) for x in p]

    def event(self, name, data=None):
        self.events.append({"type":"event", "tick":self.tick, "name":name, "data":data or {}})

    def light(self, lantern):
        return lantern["lit"]

    @property
    def time_left(self):
        return max(0.0, self.initial_time_left - self.tick / HZ)

    def step(self, inp):
        if self.state != "playing": return
        self.tick += 1
        self.invuln = max(0, self.invuln-1); self.pulse_cd = max(0, self.pulse_cd-1)
        dt = 1/HZ
        mv = inp.get("move", [0,0]); yaw = math.radians(float(inp.get("cam_yaw_deg", 0)))
        x, z = float(mv[0]), float(mv[1]); mag = math.hypot(x,z)
        if mag > 1: x,z=x/mag,z/mag
        wx, wz = x*math.cos(yaw)+z*math.sin(yaw), -x*math.sin(yaw)+z*math.cos(yaw)
        self.pos[0] += wx*T["player_speed"]*dt; self.pos[2] += wz*T["player_speed"]*dt
        if inp.get("jump") and not inp.get("_jump_prev") and self.on_ground: self.vy=T["jump_velocity_m_s"]; self.on_ground=False
        if not self.on_ground:
            self.pos[1] += self.vy*dt; self.vy -= T["gravity_m_s2"]*dt
            if self.pos[1] <= 0: self.pos[1]=0; self.vy=0; self.on_ground=True
        if inp.get("interact") and not inp.get("_interact_prev"):
            near = [l for l in self.lanterns if not l["lit"] and dist(self.pos,l["pos"]) <= T["interact_radius"]]
            if near and self.carried:
                l=min(near,key=lambda a:dist(self.pos,a["pos"]))
                amount=min(self.carried,T["lantern_cost"]-l["deposited"])
                self.carried-=amount; l["deposited"]+=amount
                self.event("deposit",{"lantern_id":l["id"],"amount":amount,"deposited":l["deposited"]})
                if l["deposited"] >= T["lantern_cost"]:
                    l["lit"]=True; self.score+=T["score"]["per_lantern"]; self.event("lantern_lit",{"lantern_id":l["id"]})
            else:
                choices=[m for m in self.motes if dist(self.pos,m["pos"])<=T["pickup_radius"]]
                if choices and self.carried<T["carry_capacity"]:
                    m=min(choices,key=lambda a:dist(self.pos,a["pos"]))
                    self.motes.remove(m); self.carried+=1; self.score+=T["score"]["per_mote"]
                    self.event("mote_picked",{"carried":self.carried})
        if inp.get("pulse") and not inp.get("_pulse_prev") and self.pulse_cd==0 and self.carried>=T["pulse_cost"]:
            self.carried-=T["pulse_cost"]; self.pulse_cd=round(T["pulse_cooldown_s"]*HZ)
            hit=[]
            for s in self.shades:
                if s["state"]!="stunned" and dist(self.pos,s["pos"])<=T["pulse_radius"]:
                    dx,dz=s["pos"][0]-self.pos[0],s["pos"][2]-self.pos[2]; d=math.hypot(dx,dz) or 1
                    s["pos"][0]+=dx/d*T["pulse_push_m"]; s["pos"][2]+=dz/d*T["pulse_push_m"]
                    s["state"]="stunned"; s["stun"]=round(T["pulse_stun_s"]*HZ); hit.append(s["id"])
                    self.score+=T["score"]["per_stun"]
            self.event("pulse",{"stunned_ids":hit})
        for s in self.shades:
            if s["state"]=="stunned":
                s["stun"]-=1
                if s["stun"]<=0: s["state"]="chase"
                continue
            if any(l["lit"] and dist(s["pos"],l["pos"])<=T["safe_radius"] for l in self.lanterns): continue
            dx,dz=self.pos[0]-s["pos"][0],self.pos[2]-s["pos"][2]; d=math.hypot(dx,dz)
            if d>0.05:
                step=min(d,T["shade_speed"]*dt); s["pos"][0]+=dx/d*step; s["pos"][2]+=dz/d*step
            if d<=T["shade_hit_radius"] and self.invuln==0:
                self.flames=max(0,self.flames-1); dropped=math.floor(self.carried*T["hit_drop_ratio"])
                self.carried-=dropped; self.invuln=round(T["invuln_s"]*HZ)
                self.event("player_hit",{"by":"shade","flames":self.flames,"dropped":dropped})
                if self.flames==0: self.finish("lost","no_flames")
                break
        if T["fall_enabled"] and math.hypot(self.pos[0],self.pos[2])>ISLAND_R and self.invuln==0 and self.state=="playing":
            self.flames=max(0,self.flames-1); dropped=math.floor(self.carried*T["hit_drop_ratio"]); self.carried-=dropped
            self.invuln=round(T["invuln_s"]*HZ); self.pos[0]*=ISLAND_R/math.hypot(self.pos[0],self.pos[2]); self.pos[2]*=ISLAND_R/math.hypot(self.pos[0],self.pos[2])
            self.event("player_hit",{"by":"fall","flames":self.flames,"dropped":dropped})
            if self.flames==0: self.finish("lost","no_flames")
        if self.state=="playing" and self.time_left<=1e-9: self.finish("lost","dawn")
        if self.state=="playing" and all(l["lit"] for l in self.lanterns): self.finish("won","all_lit")

    def finish(self, state, reason):
        self.state,self.result=state,reason
        if state=="won":
            self.score+=math.floor(self.time_left)*T["score"]["per_second_left"]+self.flames*T["score"]["per_flame_left"]
        self.event("game_over",{"result":state,"reason":reason})

    def snapshot(self):
        return {"type":"snapshot","tick":self.tick,"sim_tick":self.tick,"state":self.state,"time_left_s":round(self.time_left,3),"score":self.score,
          "player":{"pos":[round(v,3) for v in self.pos],"flames":self.flames,"carried":self.carried},
          "lanterns":[{"id":l["id"],"pos":[round(v,3) for v in l["pos"]],"lit":l["lit"],"deposited":l["deposited"]} for l in self.lanterns],
          "shades":[{"id":s["id"],"pos":[round(v,3) for v in s["pos"]],"state":s["state"]} for s in self.shades],"motes_active":len(self.motes)}


def load_json(path, kind):
    try:
        with open(path, encoding="utf-8-sig") as f:
            value = json.load(f)
    except (OSError,json.JSONDecodeError) as e: raise ValueError(f"cannot read {kind}: {e}") from e
    return value


def load_inputs(path):
    if not path: return []
    obj=load_json(path,"inputs")
    if not isinstance(obj,dict) or not isinstance(obj.get("frames"),list): raise ValueError("inputs.frames must be an array")
    frames=[]; last=-1
    for f in obj["frames"]:
        if not isinstance(f,dict) or isinstance(f.get("tick"),bool) or not isinstance(f.get("tick"),int) or f["tick"]<0 or f["tick"]<=last: raise ValueError("input ticks must be nonnegative and increase strictly")
        last=f["tick"]
        for b in ("jump","interact","pulse"):
            if b in f and not isinstance(f[b],bool): raise ValueError(f"{b} must be boolean")
        if "move" in f and (not isinstance(f["move"],list) or len(f["move"])!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or not -1<=v<=1 for v in f["move"])): raise ValueError("move components must be finite and in [-1,1]")
        if "cam_yaw_deg" in f and (isinstance(f["cam_yaw_deg"],bool) or not isinstance(f["cam_yaw_deg"],(int,float)) or not math.isfinite(f["cam_yaw_deg"])): raise ValueError("cam_yaw_deg must be finite numeric")
        frames.append(f)
    return frames


def headless(args):
    sc=load_json(args.scenario,"scenario") if args.scenario else None
    frames=load_inputs(args.inputs); fidx=0; current={"move":[0,0],"cam_yaw_deg":0,"jump":False,"interact":False,"pulse":False}
    game=Game(args.seed,sc)
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="\n") as stream:
        for event in game.events:
            stream.write(json.dumps(event,separators=(",",":"))+"\n")
        game.events.clear()
        stream.write(json.dumps(game.snapshot(),separators=(",",":"))+"\n")
        for k in range(args.ticks):
            while fidx<len(frames) and frames[fidx]["tick"]==k:
                current.update({key:value for key,value in frames[fidx].items() if key!="tick"}); fidx+=1
            if game.state!="playing": break
            current["_jump_prev"]=getattr(game,"_last_jump",False)
            current["_interact_prev"]=getattr(game,"_last_interact",False); current["_pulse_prev"]=getattr(game,"_last_pulse",False)
            game.step(current); game._last_jump=current["jump"]; game._last_interact=current["interact"]; game._last_pulse=current["pulse"]
            for event in game.events: stream.write(json.dumps(event,separators=(",",":"))+"\n")
            game.events.clear()
            if game.tick%args.snapshot_every==0: stream.write(json.dumps(game.snapshot(),separators=(",",":"))+"\n")
            if game.state!="playing": break
        stream.write(json.dumps({"type":"end","ticks":game.tick,"state":game.state,"score":game.score},separators=(",",":"))+"\n")


class GameUI:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.root=tk.Tk(); self.root.title("Đảo Đèn Lồng · Đêm 1"); self.root.geometry("960x680"); self.root.configure(bg="#10162a")
        self.canvas=tk.Canvas(self.root,bg="#10162a",highlightthickness=0); self.canvas.pack(fill="both",expand=True)
        self.game=Game(); self.keys=set(); self.tick=0; self.yaw=0; self.last=False
        # Keyboard focus normally belongs to the canvas, so root.bind alone can
        # miss key events. Bind at the application level and reclaim focus on click.
        self.root.bind_all("<KeyPress>",self.keydown); self.root.bind_all("<KeyRelease>",self.keyup)
        self.root.bind_all("<Escape>",lambda e:self.root.destroy())
        self.canvas.bind("<Button-1>",lambda e:self.canvas.focus_set())
        self.canvas.focus_set()
        self.loop()
    def keydown(self,e):
        self.keys.add(e.keysym.lower())
        if e.keysym.lower()=="r" and self.game.state!="playing": self.game=Game()
    def keyup(self,e): self.keys.discard(e.keysym.lower())
    def project(self,p):
        w=max(self.canvas.winfo_width(),1); h=max(self.canvas.winfo_height(),1); scale=min(w,h)*.012
        yaw=self.yaw; x,z=p[0]-self.game.pos[0],p[2]-self.game.pos[2]
        rx=x*math.cos(yaw)-z*math.sin(yaw); rz=x*math.sin(yaw)+z*math.cos(yaw)
        # Positive Z is forward in gameplay, so it must project upward on screen.
        # Forward objects also appear closer/larger in this perspective view.
        depth=max(10.0,42.0-rz*.35); perspective=42.0/depth
        return w/2+rx*scale*perspective,h*.58+(-rz*.55-p[1])*scale*perspective
    def draw(self):
        c=self.canvas; c.delete("all"); w=max(c.winfo_width(),1); h=max(c.winfo_height(),1)
        cx,cy=w/2,h*.58; scale=min(w,h)*.012
        shore=[]
        for i in range(64):
            a=i*2*math.pi/64; shore.extend(self.project([ISLAND_R*math.cos(a),0,ISLAND_R*math.sin(a)]))
        c.create_polygon(*shore,fill="#183c45",outline="#529491",width=3)
        # Mây of stars and island shore markers
        for i in range(32):
            a=i*math.pi/16; x,y=self.project([ISLAND_R*.96*math.cos(a),0,ISLAND_R*.96*math.sin(a)])
            c.create_oval(x-2,y-2,x+2,y+2,fill="#9bd7c0",outline="")
        for l in self.game.lanterns:
            x,y=self.project(l["pos"]); color="#ffcf70" if l["lit"] else "#69563d"
            c.create_line(x,y+11,x,y-12,fill=color,width=4); c.create_oval(x-7,y-19,x+7,y-5,fill=color,outline="#fff0b0")
            c.create_text(x,y+18,text=l["id"],fill="#f4e6bd",font=("Arial",9))
            if l["lit"]:
                # Purely visual firefly halo: no simulation entity or contract output.
                for j in range(3):
                    a=self.game.tick/HZ*1.4+j*2*math.pi/3
                    gx,gy=self.project([l["pos"][0]+math.cos(a)*1.6,0,l["pos"][2]+math.sin(a)*1.6])
                    c.create_oval(gx-2,gy-5,gx+2,gy-1,fill="#fff1a6",outline="")
        for m in self.game.motes:
            x,y=self.project(m["pos"]); c.create_oval(x-3,y-3,x+3,y+3,fill="#ffe98d",outline="")
        for s in self.game.shades:
            x,y=self.project(s["pos"]); color="#a478d1" if s["state"]=="stunned" else "#351c50"
            c.create_oval(x-10,y-12,x+10,y+8,fill=color,outline="#c7a7ef",width=2)
        x,y=self.project(self.game.pos)
        c.create_oval(x-9,y-11,x+9,y+11,fill="#f1c7aa",outline="#fff0d0"); c.create_polygon(x-13,y-9,x,y-23,x+13,y-9,fill="#a98445",outline="#f0d78e")
        c.create_rectangle(x+8,y-1,x+17,y+9,fill="#ffc95c",outline="#ffe7a8")
        lit=sum(l["lit"] for l in self.game.lanterns)
        c.create_rectangle(18,16,464,122,fill="#10162a",outline="#48516a"); c.create_text(34,33,anchor="w",text=f"ĐÊM 1 · ĐẢO BẾN     Đèn {lit}/5",fill="#ffe0a0",font=("Arial",16,"bold"))
        c.create_text(34,61,anchor="w",text=f"Lửa {self.game.flames}   Đom đóm {self.game.carried}/5   Điểm {self.game.score}",fill="white",font=("Arial",12))
        # Show each lantern's deposited motes so players can see partial progress.
        c.create_text(34,91,anchor="w",text="TIẾN ĐỘ ĐÈN",fill="#c5c9d6",font=("Arial",9,"bold"))
        for i, lantern in enumerate(self.game.lanterns):
            bx, by = 112+i*66, 84
            c.create_text(bx,by,anchor="w",text=lantern["id"],fill="#ffe0a0" if lantern["lit"] else "#d6d0c1",font=("Arial",9,"bold"))
            c.create_rectangle(bx,by+13,bx+48,by+20,fill="#393949",outline="")
            if lantern["deposited"]:
                c.create_rectangle(bx,by+13,bx+48*lantern["deposited"]/T["lantern_cost"],by+20,
                                   fill="#ffbd58" if lantern["lit"] else "#a98445",outline="")
            c.create_text(bx+51,by+16,text="✓" if lantern["lit"] else f"{lantern['deposited']}/5",fill="#ffe0a0",font=("Arial",8))
        c.create_text(w-20,25,anchor="e",text=f"{max(0,int(self.game.time_left))//60:02}:{max(0,int(self.game.time_left))%60:02}",fill="#ffe0a0",font=("Arial",18,"bold"))
        c.create_text(w/2,h-22,text="WASD di chuyển · Space nhảy · E nhặt/nạp · Q xung sáng · ← → xoay camera · R chơi lại",fill="#e7e5de",font=("Arial",11))
        if self.game.state!="playing":
            c.create_rectangle(w*.25,h*.34,w*.75,h*.64,fill="#10162a",outline="#ffdb94",width=3)
            title="ĐẢO ĐÃ SÁNG!" if self.game.state=="won" else "ĐÊM TỐI THẮNG THẾ"
            c.create_text(w/2,h*.43,text=title,fill="#ffe0a0",font=("Arial",27,"bold")); c.create_text(w/2,h*.52,text=f"Điểm {self.game.score}  ·  Nhấn R để chơi lại",fill="white",font=("Arial",15))
    def loop(self):
        if self.game.state=="playing":
            if "left" in self.keys:self.yaw-=.035
            if "right" in self.keys:self.yaw+=.035
            mv=[float("d" in self.keys)-float("a" in self.keys),float("w" in self.keys)-float("s" in self.keys)]
            now={"move":mv,"cam_yaw_deg":math.degrees(self.yaw),"jump":"space" in self.keys,"interact":"e" in self.keys,"pulse":"q" in self.keys,
                 "_jump_prev":self.last_jump,"_interact_prev":self.last_e,"_pulse_prev":self.last_q}
            self.game.step(now); self.last_jump=now["jump"]; self.last_e=now["interact"]; self.last_q=now["pulse"]
        self.draw(); self.root.after(16,self.loop)
    last_jump=False; last_e=False; last_q=False
    def run(self): self.root.mainloop()


def main():
    p=argparse.ArgumentParser(description="Đảo Đèn Lồng")
    p.add_argument("--headless",action="store_true"); p.add_argument("--seed",type=int,default=1); p.add_argument("--night",type=int,default=1)
    p.add_argument("--scenario"); p.add_argument("--inputs"); p.add_argument("--ticks",type=int,default=18000); p.add_argument("--out",default="out.jsonl"); p.add_argument("--snapshot-every",type=int,default=10)
    a=p.parse_args()
    try:
        if a.night!=1: raise ValueError("only --night 1 is supported in Phase 1")
        if a.ticks<0 or a.snapshot_every<=0: raise ValueError("ticks must be >= 0 and snapshot-every must be > 0")
        if a.headless: headless(a)
        else: GameUI().run()
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        print(f"error: {e}",file=sys.stderr); return 2
    return 0

if __name__=="__main__": raise SystemExit(main())
