import glob
import sys
import xml.etree.ElementTree as ET


def leer_reporte(ruta):
    raiz = ET.parse(ruta).getroot()
    suites = [raiz] if raiz.tag == "testsuite" else raiz.findall("testsuite")
    total = sum(int(s.get("tests", 0)) for s in suites)
    fallidas = sum(int(s.get("failures", 0)) for s in suites)
    errores = sum(int(s.get("errors", 0)) for s in suites)
    omitidas = sum(int(s.get("skipped", 0)) for s in suites)
    return total, fallidas, errores, omitidas


def main(argumentos):
    estricto = "--estricto" in argumentos
    patrones = [a for a in argumentos if a != "--estricto"]
    archivos = sorted({f for p in patrones for f in glob.glob(p)})

    if not archivos:
        print("No se encontraron reportes de pruebas (resultados-*.xml).")
        return 1

    print("### Resultados de las pruebas\n")
    print("| Reporte | Total | Pasaron | Fallidas | Errores | Omitidas |")
    print("|---|---:|---:|---:|---:|---:|")

    suma = [0, 0, 0, 0]
    for ruta in archivos:
        total, fallidas, errores, omitidas = leer_reporte(ruta)
        pasaron = total - fallidas - errores - omitidas
        print(f"| {ruta} | {total} | {pasaron} | {fallidas} | {errores} | {omitidas} |")
        for i, valor in enumerate((total, fallidas, errores, omitidas)):
            suma[i] += valor

    total, fallidas, errores, omitidas = suma
    print(f"| **TOTAL** | {total} | {total - fallidas - errores - omitidas} "
          f"| {fallidas} | {errores} | {omitidas} |\n")

    if estricto and (fallidas or errores or omitidas):
        print("RECHAZADO: hay pruebas fallidas, con error u omitidas.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))