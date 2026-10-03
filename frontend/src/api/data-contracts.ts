/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/** EpochPrediction */
export interface EpochPrediction {
  /** Epoch */
  epoch: number;
  /** Predicted Class */
  predicted_class: number;
  /** Predicted Label */
  predicted_label: string;
  /** Predicted Prob */
  predicted_prob: number;
  /** True Class Prob */
  true_class_prob: number;
  /** Probs */
  probs: number[];
}

/** GradCamResponse */
export interface GradCamResponse {
  /** True Class */
  true_class: number;
  /** True Label */
  true_label: string;
  /** Original */
  original: string;
  epoch_a: GradCamSide;
  epoch_b: GradCamSide;
  /** Diff */
  diff: string;
}

/** GradCamSide */
export interface GradCamSide {
  /** Epoch */
  epoch: number;
  /** Cam */
  cam: string;
  /** Predicted Class */
  predicted_class: number;
  /** Predicted Label */
  predicted_label: string;
  /** Predicted Prob */
  predicted_prob: number;
  /** Probs */
  probs: number[];
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/** MetaResponse */
export interface MetaResponse {
  /** Epochs */
  epochs: number[];
  /** Classes */
  classes: string[];
}

/** PredictionsResponse */
export interface PredictionsResponse {
  /** True Class */
  true_class: number;
  /** True Label */
  true_label: string;
  /** Predictions */
  predictions: EpochPrediction[];
}

/** Sample */
export interface Sample {
  /** Index */
  index: number;
  /** Label */
  label: number;
  /** Label Name */
  label_name: string;
  /** Thumbnail */
  thumbnail: string;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
  /** Input */
  input?: any;
  /** Context */
  ctx?: object;
}
