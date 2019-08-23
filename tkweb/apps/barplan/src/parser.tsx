import { app } from "./app";

class Parser {
  parsePlanToLaTeXString() {
    const columnSpecification = "c".repeat(app.locationNames.length);
    const headerRow = app.locationNames.map(
      location => `\\textbf{${location}}`
    );
    const header = `\\centering
\\hspace*{-1.5cm}\\begin{tabular}{l|${columnSpecification}l}
\\toprule
\\textbf{Tid.} & ${headerRow.join(" & ")}\\\\
\\midrule`;
    const rows = [];
    for (const [t, time] of app.timeNames.entries()) {
      const cells = [];
      for (let l = 0; l < app.locationNames.length; l++) {
        if (!app.workslotClosed(t, l)) {
          const supervisor = app.supervisorExists(t, l);
          let workers = app.persons
            .map((_, i) => i)
            .filter(i => app.isPersonInSlot(i, t, l));
          const people = [];
          if (supervisor !== null) {
            people.push(
              "\\textbf{" +
                this.checkForSpecialNaming(app.persons[supervisor]) +
                "}"
            );
            workers = workers.filter(i => i !== supervisor);
          }
          people.push(
            ...workers.map(i => this.checkForSpecialNaming(app.persons[i]))
          );
          cells.push(people.join(" "));
        } else {
          cells.push(" -- ");
        }
      }
      rows.push(`${time} & ${cells.join(" & ")}\\\\`);
    }
    return `${header}
${rows.join("\n")}
\\bottomrule
\\end{tabular}`;
  }

  checkForSpecialNaming(name: string): string {
    name = name.replace("KASS", "\\KASS");
    name = name.replace("KA$$", "\\KASS");
    name = name.replace("VC", "\\VC");
    name = name.replace("CERM", "\\CERM");
    return name;
  }

  parsePlanToCSVString() {
    let rows = "\t";
    for (const location of app.locationNames) {
      rows += location + "\t";
    }
    rows += "\n";
    for (const [t, time] of app.timeNames.entries()) {
      rows += time + "\t";
      for (let l = 0; l < app.locationNames.length; l++) {
        let supervisor = app.supervisorExists(t, l);
        let workers = app.persons
          .map((_, i) => i)
          .filter(i => app.isPersonInSlot(i, t, l));
        if (supervisor !== null) {
          rows += "[" + app.persons[supervisor] + "]" + " ";
          workers = workers.filter(i => i !== supervisor);
        }
        for (const i of workers) {
          rows += app.persons[i] + " ";
        }
        rows += "\t";
      }
      rows += "\n";
    }
    return rows;
  }
}

export const parser = new Parser();
