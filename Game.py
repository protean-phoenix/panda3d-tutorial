from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import AmbientLight
from panda3d.core import CollisionHandlerPusher
from panda3d.core import CollisionNode
from panda3d.core import CollisionSphere
from panda3d.core import CollisionTraverser
from panda3d.core import CollisionTube
from panda3d.core import DirectionalLight
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import WindowProperties

from GameObject import *


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        properties = WindowProperties()
        properties.set_size(1000, 750)
        self.win.requestProperties(properties)
        self.disable_mouse()

        self.environment = loader.loadModel("Models/Misc/environment")
        self.environment.reparentTo(render)

        self.camera.setPos(0,0,32)
        self.camera.setP(-90)

        mainLight = DirectionalLight("main light")
        self.mainLightNodePath = render.attachNewNode(mainLight)
        self.mainLightNodePath.setHpr(45,-45,0)
        render.setLight(self.mainLightNodePath)

        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        self.ambientLightNodePath = render.attachNewNode(ambientLight)
        render.setLight(self.ambientLightNodePath)

        render.setShaderAuto()

        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.setHorizontal(True)
        self.pusher.add_in_pattern("%fn-into-%in")

        self.accept("trapEnemy-into-wall", self.stopTrap)
        self.accept("trapEnemy-into-trapEnemy", self.stopTrap)
        self.accept("trapEnemy-into-player", self.trapHitsSomething)
        self.accept("trapEnemy-into-walkingEnemy", self.trapHitsSomething)

        wallSolid = CollisionTube(-8.0, 0, 0, 8.0, 0, 0, 0.2)
        wallNode = CollisionNode("wall")
        wallNode.addSolid(wallSolid)
        wall = render.attachNewNode(wallNode)
        wall.setY(8.0)

        wallSolid = CollisionTube(-8.0, 0, 0, 8.0, 0, 0, 0.2)
        wallNode = CollisionNode("wall")
        wallNode.addSolid(wallSolid)
        wall = render.attachNewNode(wallNode)
        wall.setY(-8.0)

        wallSolid = CollisionTube(0, -8.0, 0, 0, 8.0, 0, 0.2)
        wallNode = CollisionNode("wall")
        wallNode.addSolid(wallSolid)
        wall = render.attachNewNode(wallNode)
        wall.setX(8.0)

        wallSolid = CollisionTube(0, -8.0, 0, 0, 8.0, 0, 0.2)
        wallNode = CollisionNode("wall")
        wallNode.addSolid(wallSolid)
        wall = render.attachNewNode(wallNode)
        wall.setX(-8.0)

        self.keyMap = {
            "up": False,
            "down": False,
            "right": False,
            "left": False,
            "shoot": False
        }

        self.accept("w", self.updateKeyMap, ["up", True])
        self.accept("w-up", self.updateKeyMap, ["up", False])
        self.accept("s", self.updateKeyMap, ["down", True])
        self.accept("s-up", self.updateKeyMap, ["down", False])
        self.accept("a", self.updateKeyMap, ["left", True])
        self.accept("a-up", self.updateKeyMap, ["left", False])
        self.accept("d", self.updateKeyMap, ["right", True])
        self.accept("d-up", self.updateKeyMap, ["right", False])
        self.accept("mouse1", self.updateKeyMap, ["shoot", True])
        self.accept("mouse1-up", self.updateKeyMap, ["shoot", False])

        self.updateTask = taskMgr.add(self.update, "update")

        self.player = Player()
        self.tempEnemy = WalkingEnemy(Vec3(5, 0, 0))
        self.tempTrap = TrapEnemy(Vec3(-2, 7, 0))

    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    def update(self, task):
        # Get time since last update
        dt = globalClock.getDt()
        self.player.update(self.keyMap, dt)
        self.tempEnemy.update(self.player, dt)
        self.tempTrap.update(self.player, dt)

        return task.cont

    def stopTrap(self, entry):
        collider = entry.getFromNodePath()
        if collider.hasPythonTag("owner"):
            trap = collider.getPythonTag("owner")
            trap.moveDirection = 0
            trap.ignorePlayer = False

    def trapHitsSomething(self, entry):
        collider = entry.getFromNodePath()
        if collider.hasPythonTag("owner"):
            trap = collider.getPythonTag("owner")

            # We don't want stationary traps to do damage,
            # so ignore the collision if the "moveDirection" is 0
            if trap.moveDirection == 0:
                return

            collider = entry.getIntoNodePath()
            if collider.hasPythonTag("owner"):
                obj = collider.getPythonTag("owner")
                if isinstance(obj, Player):
                    if not trap.ignorePlayer:
                        obj.alterHealth(-1)
                        trap.ignorePlayer = True
                else:
                    obj.alterHealth(-10)

game = Game()
game.run()
