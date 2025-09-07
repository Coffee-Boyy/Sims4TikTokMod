from animation import animation_constantsfrom interactions.social.social_super_interaction import SocialSuperInteraction
class VariableDistanceInteraction(SocialSuperInteraction):

    def setup_asm_default(self, asm, *args, **kwargs):
        result = super().setup_asm_default(asm, *args, **kwargs)
        if not result:
            return result
        if not asm.set_actor_parameter('x', self.sim, animation_constants.ASM_INITIAL_TRANSLATION, self.sim.position):
            return False
        if not asm.set_actor_parameter('x', self.sim, animation_constants.ASM_INITIAL_ORIENTATION, self.sim.orientation):
            return False
        if not asm.set_actor_parameter('x', self.sim, animation_constants.ASM_TARGET_TRANSLATION, self.target.position):
            return False
        elif not asm.set_actor_parameter('x', self.sim, animation_constants.ASM_TARGET_ORIENTATION, self.target.orientation):
            return False
        return True
