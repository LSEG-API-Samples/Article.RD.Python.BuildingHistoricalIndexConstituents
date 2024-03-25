import refinitiv.data as rd
import pandas as pd
import copy

rd.open_session()

class IndexConstituents:

    def get_historical_constituents(self, index, start, end):
        initial_constituents = self.get_constutents_as_of(index, start)
        constituent_changes = self.get_constituent_changes(index, start, end)
        historical_constituents = self.update_constituents(start, initial_constituents, constituent_changes)
        return historical_constituents

    def get_constutents_as_of(self, ric, date):
        initial_constituents = rd.get_data(universe=[f"0#{ric}({date.replace('-', '')})"], 
                    fields=["TR.PriceClose"],
                    parameters={"SDATE":f"{date}", "EDATE":f"{date}"}
                )
        initial_constituents = initial_constituents['Instrument'].to_list()
        return initial_constituents
    
    def get_constituent_changes(self, ric, start, end):

        const_changes  = rd.get_data(universe=[ric], 
                    fields = ["TR.IndexJLConstituentRIC.date", "TR.IndexJLConstituentRIC",
                            "TR.IndexJLConstituentName", "TR.IndexJLConstituentRIC.change"],
                    parameters={"SDATE":f"{start}","EDATE":f"{end}", 'IC':'B'}
                )
        
        return const_changes

    def update_constituents(self, start, constituents, constitent_changes):
        
        hist_constituents = pd.DataFrame([(start, ric) for ric in constituents], columns=['Date', 'RIC'])
        for date in constitent_changes['Date'].unique():
            const_changes_date = constitent_changes[constitent_changes['Date'] == date]
            joiners = const_changes_date[const_changes_date['Change']=='Joiner']['Constituent RIC'].to_list()
            leavers = const_changes_date[const_changes_date['Change']=='Leaver']['Constituent RIC'].to_list()
            joiners_unique = list(set(joiners) - set(leavers))
            leavers_unique = list(set(leavers) - set(joiners))
            if len(joiners_unique) > 0:
                constituents = self.add_joiner(constituents, joiners_unique)
            if len(leavers_unique) > 0:
                constituents = self.remove_leaver(constituents, leavers_unique)
            new_constituents = copy.deepcopy(constituents)
            new_constituents_df =  pd.DataFrame([(str(date)[:10], ric) for ric in new_constituents], columns=['Date', 'RIC'])
            hist_constituents = pd.concat([hist_constituents, new_constituents_df])
        hist_constituents = hist_constituents.reset_index(drop = True)
        
        return hist_constituents
    
    def add_joiner(self, init_list, joiner_list):
        for joiner in joiner_list:
            if joiner not in init_list:
                init_list.append(joiner)
            else:
                print(f'{joiner} joiner is already in the list')
        return init_list

    def remove_leaver(self, init_list, leaver_list):
        for leaver in leaver_list:
            if leaver in init_list:
                init_list.remove(leaver)
            else:
                print(f'{leaver} leaver is not in the list')
        return init_list

# Usage Example

# ic = IndexConstituents()
# ftse_historical = ic.get_historical_constituents(index= '.FTSE', start = '2014-01-01', end = '2024-02-15')
# print(ftse_historical)