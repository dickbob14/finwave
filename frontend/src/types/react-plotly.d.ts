declare module 'react-plotly.js' {
  import * as React from 'react';

  export interface PlotParams {
    data: any[];
    layout?: any;
    config?: any;
    frames?: any[];
    revision?: number;
    onInitialized?: (figure: any, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: any, graphDiv: HTMLElement) => void;
    onPurge?: (figure: any, graphDiv: HTMLElement) => void;
    onError?: (err: Error) => void;
    divId?: string;
    className?: string;
    style?: React.CSSProperties;
    debug?: boolean;
    useResizeHandler?: boolean;
  }

  export default class Plot extends React.PureComponent<PlotParams> {}
}