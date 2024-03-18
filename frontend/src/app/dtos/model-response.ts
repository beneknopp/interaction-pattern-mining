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

export class PartitionResponse {
    antecedent_ids: string[]
    pretty_antecedent_ids: string[]
    model_responses: { [partition_id: number]: ModelResponse }

    constructor(
        antecedent_ids: string[],
        pretty_antecedent_ids: string[],
        model_responses: { [partition_id: number]: ModelResponse }
    ) {
        this.antecedent_ids = antecedent_ids
        this.pretty_antecedent_ids = pretty_antecedent_ids
        this.model_responses = model_responses
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