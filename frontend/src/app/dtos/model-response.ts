import { ObjectType } from "./utils"

export class ModelEvaluation {
    precision: number
    recall: number
    discrimination: number
    simplicity: number
    constructor(
        precision: number,
        recall: number,
        discrimination: number,
        simplicity: number
    ) {
        this.precision = precision
        this.recall = recall
        this.discrimination = discrimination
        this.simplicity = simplicity
    }
}

export class ModelResponse {
    valid_patterns: PartitionResponse
    partitions: {[partition_id: number]: PartitionResponse}
    constructor(
        valid_patterns: PartitionResponse,
        partitions: {[partition_id: number]: PartitionResponse}
    ) {
        this.valid_patterns = valid_patterns
        this.partitions = partitions
    }
}

export class PartitionResponse {
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

export class SplitResponse {
    response: {
        [partition: number]: PartitionResponse
    }
    constructor(
        response: { [partition: number]: PartitionResponse }
    ) {
        this.response = response
    }
}