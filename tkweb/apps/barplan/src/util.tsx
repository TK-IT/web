export function classNames(classes: { [className: string]: any }) {
  let classNames = [];
  for (const k in classes) {
    if (classes[k]) classNames.push(k);
  }
  return classNames.join(" ");
}
