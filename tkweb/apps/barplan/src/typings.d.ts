declare module "*.scss" {
    const classNames: { [className: string]: string };
    export default classNames;
}

declare module "*.txt" {
    const contents: string;
    export default contents;
}
