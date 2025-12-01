from __future__ import annotations


def main() -> None:
    C_solid = 143.0
    C_sat = 5.1

    CSe = C_solid / C_solid
    CLe = C_sat / C_solid

    print(f"CSe = {CSe:.4f}")
    print(f"CLe = {CLe:.4f}")


if __name__ == "__main__":
    main()
