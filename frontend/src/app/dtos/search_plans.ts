import { EventType, ObjectType, PatternID } from "./utils"

export enum PatternType {
    Basic = 'basic_patterns',
    Interaction = 'interaction_patterns',
    Custom = 'custom_patterns'
  }

export interface SearchPlans{

    patterns: {[eventType: EventType]: {
        [PatternType.Basic]: PatternID[],
        [PatternType.Interaction]: {
            [objectType: ObjectType]: PatternID[]
        },
        [PatternType.Custom]: PatternID[]
    }}

    
}

