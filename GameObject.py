import math

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode

FRICTION = 150.0


class GameObject():
    def __init__(self, pos, modelName, modelAnims, maxHealth, maxSpeed, colliderName):
        self.actor = Actor(modelName, modelAnims)
        self.actor.reparentTo(render)
        self.actor.setPos(pos)

        self.maxHealth = maxHealth
        self.health = maxHealth

        self.maxSpeed = maxSpeed

        self.velocity = Vec3(0, 0, 0)
        self.acceleration = 300.0

        self.walking = False

        # Note the "colliderName"--this will be used for
        # collision-events, later...
        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 0, 0.3))
        self.collider = self.actor.attachNewNode(colliderNode)
        # See below for an explanation of this!
        self.collider.setPythonTag("owner", self)

    def update(self, dt):
        # If we're going faster than our maximum speed,
        # set the velocity-vector's length to that maximum
        speed = self.velocity.length()
        if speed > self.maxSpeed:
            self.velocity.normalize()
            self.velocity *= self.maxSpeed
            speed = self.maxSpeed

        # If we're walking, don't worry about friction.
        # Otherwise, use friction to slow us down.
        if not self.walking:
            frictionVal = FRICTION*dt
            if frictionVal > speed:
                self.velocity.set(0, 0, 0)
            else:
                frictionVec = -self.velocity
                frictionVec.normalize()
                frictionVec *= frictionVal

                self.velocity += frictionVec

        # Move the character, using our velocity and
        # the time since the last update.
        self.actor.setPos(self.actor.getPos() + self.velocity*dt)

    def alterHealth(self, dHealth):
        self.health += dHealth

        if self.health > self.maxHealth:
            self.health = self.maxHealth

    def cleanup(self):
        # Remove various nodes, and clear the Python-tag--see below!

        if self.collider is not None and not self.collider.isEmpty():
            self.collider.clearPythonTag("owner")
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        if self.actor is not None:
            self.actor.cleanup()
            self.actor.removeNode()
            self.actor = None

        self.collider = None


class Player(GameObject):
    def __init__(self):
        GameObject.__init__(self,
                            Vec3(0, 0, 0),
                            "Models/PandaChan/act_p3d_chan",
                              {
                                  "stand" : "Models/PandaChan/a_p3d_chan_idle",
                                  "walk" : "Models/PandaChan/a_p3d_chan_run"
                              },
                            5,
                            10,
                            "player")

        # Panda-chan faces "backwards", so we just turn
        # the first sub-node of our Actor-NodePath
        # to have it face as we want.
        self.actor.getChild(0).setH(180)

        # Since our "Game" object is the "ShowBase" object,
        # we can access it via the global "base" variable.
        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.actor.loop("stand")

    def update(self, keys, dt):
        GameObject.update(self, dt)

        self.walking = False

        # If we're  pushing a movement key, add a relevant amount
        # to our velocity.
        if keys["up"]:
            self.walking = True
            self.velocity.addY(self.acceleration*dt)
        if keys["down"]:
            self.walking = True
            self.velocity.addY(-self.acceleration*dt)
        if keys["left"]:
            self.walking = True
            self.velocity.addX(-self.acceleration*dt)
        if keys["right"]:
            self.walking = True
            self.velocity.addX(self.acceleration*dt)

        # Run the appropriate animation for our current state.
        # See the text below this for an explanation
        if self.walking:
            standControl = self.actor.getAnimControl("stand")
            if standControl.isPlaying():
                standControl.stop()

            walkControl = self.actor.getAnimControl("walk")
            if not walkControl.isPlaying():
                self.actor.loop("walk")
        else:
            standControl = self.actor.getAnimControl("stand")
            if not standControl.isPlaying():
                self.actor.stop("walk")
                self.actor.loop("stand")


class Enemy(GameObject):
    def __init__(self, pos, modelName, modelAnims, maxHealth, maxSpeed, colliderName):
        GameObject.__init__(self, pos, modelName, modelAnims, maxHealth, maxSpeed, colliderName)

        # This is the number of points to award
        # if the enemy is killed.
        self.scoreValue = 1

    def update(self, player, dt):
        # In short, update as a GameObject, then
        # run whatever enemy-specific logic is to be done.
        # The use of a separate "runLogic" method
        # allows us to customise that specific logic
        # to the enemy, without re-writing the rest.

        GameObject.update(self, dt)

        self.runLogic(player, dt)

        # As with the player, play the appropriate animation.
        if self.walking:
            walkingControl = self.actor.getAnimControl("walk")
            if not walkingControl.isPlaying():
                self.actor.loop("walk")
        else:
            spawnControl = self.actor.getAnimControl("spawn")
            if spawnControl is None or not spawnControl.isPlaying():
                attackControl = self.actor.getAnimControl("attack")
                if attackControl is None or not attackControl.isPlaying():
                    standControl = self.actor.getAnimControl("stand")
                    if not standControl.isPlaying():
                        self.actor.loop("stand")

    def runLogic(self, player, dt):
        pass


class WalkingEnemy(Enemy):
    def __init__(self, pos):
        Enemy.__init__(self, pos,
                       "Models/Misc/simpleEnemy",
                       {
                        "stand" : "Models/Misc/simpleEnemy-stand",
                        "walk" : "Models/Misc/simpleEnemy-walk",
                        "attack" : "Models/Misc/simpleEnemy-attack",
                        "die" : "Models/Misc/simpleEnemy-die",
                        "spawn" : "Models/Misc/simpleEnemy-spawn"
                        },
                       3.0,
                       7.0,
                       "walkingEnemy")

        self.attackDistance = 0.75

        self.acceleration = 100.0

        # A reference vector, used to determine
        # which way to face the Actor.
        # Since the character faces along
        # the y-direction, we use the y-axis.
        self.yVector = Vec2(0, 1)

    def runLogic(self, player, dt):
        # In short: find the vector between
        # this enemy and the player.
        # If the enemy is far from the player,
        # use that vector to move towards the player.
        # Otherwise, just stop for now.
        # Finally, face the player.

        vectorToPlayer = player.actor.getPos() - self.actor.getPos()

        vectorToPlayer2D = vectorToPlayer.getXy()
        distanceToPlayer = vectorToPlayer2D.length()

        vectorToPlayer2D.normalize()

        heading = self.yVector.signedAngleDeg(vectorToPlayer2D)

        if distanceToPlayer > self.attackDistance*0.9:
            self.walking = True
            vectorToPlayer.setZ(0)
            vectorToPlayer.normalize()
            self.velocity += vectorToPlayer*self.acceleration*dt
        else:
            self.walking = False
            self.velocity.set(0, 0, 0)

        self.actor.setH(heading)


class TrapEnemy(Enemy):
    def __init__(self, pos):
        Enemy.__init__(self, pos,
                       "Models/Misc/trap",
                       {
                        "stand" : "Models/Misc/trap-stand",
                        "walk" : "Models/Misc/trap-walk",
                        },
                       100.0,
                       10.0,
                       "trapEnemy")

        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.moveInX = False

        self.moveDirection = 0

        # This will allow us to prevent multiple
        # collisions with the player during movement
        self.ignorePlayer = False

    def runLogic(self, player, dt):
        if self.moveDirection != 0:
            self.walking = True
            if self.moveInX:
                self.velocity.addX(self.moveDirection*self.acceleration*dt)
            else:
                self.velocity.addY(self.moveDirection*self.acceleration*dt)
        else:
            self.walking = False
            diff = player.actor.getPos() - self.actor.getPos()
            if self.moveInX:
                detector = diff.y
                movement = diff.x
            else:
                detector = diff.x
                movement = diff.y

            if abs(detector) < 0.5:
                self.moveDirection = math.copysign(1, movement)

    def alterHealth(self, dHealth):
        pass
