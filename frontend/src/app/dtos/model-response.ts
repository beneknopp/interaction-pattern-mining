import { ObjectType } from "./utils"

export class Partition {
    support: number
    pretty_pattern_ids: string[]
    pattern_ids: string[]
    argument_ids: { [objectType: ObjectType]: string[] }
    constructor(
        support: number,
        pretty_pattern_ids: string[],
        pattern_ids: string[],
        argument_ids: { [objectType: ObjectType]: string[] }
    ) {
        this.support = support
        this.pretty_pattern_ids = pretty_pattern_ids
        this.pattern_ids = pattern_ids
        this.argument_ids = argument_ids
    }
}

export class ModelResponse {
    response: {
        [partition: number]: Partition
    }
    constructor(
        response: {[partition: number]: Partition}
    ) {
        this.response = response
    }
}

