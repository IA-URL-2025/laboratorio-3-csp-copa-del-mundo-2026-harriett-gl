import copy


class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        """
        Inicializa el problema CSP para el sorteo del Mundial.
        :param teams: Diccionario con los equipos, sus confederaciones y bombos.
        :param groups: Lista con los nombres de los grupos (A-L).
        :param debug: Booleano para activar trazas de depuración.
        """
        self.teams = teams
        self.groups = groups
        self.debug = debug

        # Las variables son los equipos.
        self.variables = list(teams.keys())

        # El dominio de cada variable inicialmente son todos los grupos.
        self.domains = {team: list(groups) for team in self.variables}

    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def is_valid_assignment(self, group, team, assignment):
        """
        Verifica si asignar un equipo a un grupo viola las restricciones:
        - máximo 4 equipos por grupo
        - no puede haber dos equipos del mismo bombo en el mismo grupo
        - confederaciones:
            * UEFA: máximo 2 por grupo
            * otras: máximo 1 por grupo
        """

        # Equipos ya asignados a ese grupo
        teams_in_group = [t for t, g in assignment.items() if g == group]

        # 1) tamaño máximo del grupo
        if len(teams_in_group) >= 4:
            return False

        team_pot = self.get_team_pot(team)
        team_conf = self.get_team_confederation(team)

        uefa_count = 0

        for assigned_team in teams_in_group:
            assigned_pot = self.get_team_pot(assigned_team)
            assigned_conf = self.get_team_confederation(assigned_team)

            # 2) restricción de bombo
            if assigned_pot == team_pot:
                return False

            # contar UEFA ya presentes
            if assigned_conf == "UEFA":
                uefa_count += 1

            # 3) restricción de confederación no UEFA
            if team_conf != "UEFA" and assigned_conf == team_conf:
                return False

        # 4) restricción UEFA
        if team_conf == "UEFA" and uefa_count >= 2:
            return False

        return True

    def forward_check(self, assignment, domains):
        """
        Propagación de restricciones.
        Debe eliminar valores inconsistentes en dominios futuros.
        Retorna True si la propagación es exitosa, False si algún dominio queda vacío.
        """
        new_domains = copy.deepcopy(domains)

        for var in self.variables:
            if var not in assignment:
                valid_values = []

                for group in new_domains[var]:
                    if self.is_valid_assignment(group, var, assignment):
                        valid_values.append(group)

                new_domains[var] = valid_values

                if len(new_domains[var]) == 0:
                    return False, new_domains

        return True, new_domains

    def select_unassigned_variable(self, assignment, domains):
        """
        Heurística MRV (Minimum Remaining Values).
        Selecciona la variable no asignada con el dominio más pequeño.
        """
        unassigned_vars = [v for v in self.variables if v not in assignment]

        if not unassigned_vars:
            return None

        return min(unassigned_vars, key=lambda var: len(domains[var]))

    def backtrack(self, assignment, domains=None):
        """
        Backtracking search para resolver el CSP.
        """
        if domains is None:
            domains = copy.deepcopy(self.domains)

        # condición de parada
        if len(assignment) == len(self.variables):
            return assignment

        # 1) seleccionar variable con MRV
        var = self.select_unassigned_variable(assignment, domains)

        if var is None:
            return assignment

        # 2) iterar sobre valores posibles
        for group in domains[var]:
            # 3) verificar si es válido
            if self.is_valid_assignment(group, var, assignment):
                assignment[var] = group

                if self.debug:
                    print(f"Asignando {var} -> {group}")

                # aplicar forward checking
                success, new_domains = self.forward_check(assignment, domains)

                if success:
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result

                # 5) deshacer asignación
                if self.debug:
                    print(f"Backtrack en {var} -> {group}")

                del assignment[var]

        return None