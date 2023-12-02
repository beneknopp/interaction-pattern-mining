import { Attribute, EventType, ObjectType, Qualifier } from "./utils"

export class UploadResponse{

    session_key: string
    event_types: EventType[]
    object_types: ObjectType[]
    event_type_attributes : {
        [eventType: EventType]: Attribute[]
    }
    event_type_object_types: {
        [eventType: EventType]: ObjectType[]
    }
    event_type_object_relations: {
        [eventType: EventType]: {
            [objectType: ObjectType]: Qualifier[]
        }
    }
    event_type_object_to_object_relations: {
        [eventType: EventType]: {
            [objectType: ObjectType]: {
                [objectType: ObjectType]: Qualifier[]
            }
        }
    }
    object_type_attributes: {[objectType: ObjectType]: Attribute[]}
    variable_prefixes: {[objectType: ObjectType]: string}

    constructor(
        session_key: string,
        event_types: [EventType],
        object_types: [objectType: ObjectType],
        event_type_attributes : {[eventType: EventType]: Attribute[]},
        event_type_object_types: {[eventType: EventType]: ObjectType[]},
        event_type_object_relations: {[eventType: EventType]: {[objectType: ObjectType]: Qualifier[]}},
        event_type_object_to_object_relations: {[eventType: EventType]: {[objectType: ObjectType]: {[objectType: ObjectType]: Qualifier[]}}},
        object_type_attributes: {[objectType: ObjectType]: Attribute[]},
        variable_prefixes: {[objectType: ObjectType]: string}
    ){
        this.session_key = session_key,
        this.event_types = event_types,
        this.object_types = object_types,
        this.event_type_attributes = event_type_attributes,
        this.event_type_object_types = event_type_object_types,
        this.event_type_object_relations = event_type_object_relations,
        this.event_type_object_to_object_relations = event_type_object_to_object_relations,
        this.object_type_attributes = object_type_attributes,
        this.variable_prefixes = variable_prefixes
    }
}

