import chess.uci
import sys

reload(sys)
sys.setdefaultencoding("latin-1")

import logging

# logging.basicConfig(level=logging.DEBUG)

sys.path.append("C:/Users/Alfonso/workspace_luna/lucaschess_11\\./Engines/Windows\\_tools")

from Code import PGN


class Reg:
    pass

def read_level(file):

    with open(file) as f:
        liTactics = []
        for linea in f:
            linea = linea.strip()
            if linea:
                reg = Reg()
                split = linea.split("|")
                reg.fen, reg.label, reg.pgn = split[0], split[1], split[2]
                liTactics.append(reg)
        #random.shuffle(liTactics)
        liPosTactics = [0, 1, 2]
        for n in range(len(liTactics) - 3):
            liPosTactics.append(n + 3)
            liPosTactics.append(n)
        liPosTactics.extend([n + 1, n + 2, n + 3])

    return liTactics

def truncFen(fen):
    sp1 = fen.rfind(" ")
    sp2 = fen.rfind(" ", 0, sp1)
    return fen[:sp2]

def oldstyle_fen(board):
    builder = []
    builder.append(board.board_fen())
    builder.append("w" if board.turn == chess.WHITE else "b")
    builder.append(board.castling_xfen())
    builder.append(chess.SQUARE_NAMES[board.ep_square] if board.ep_square else "-")
    builder.append(str(board.halfmove_clock))
    builder.append(str(board.fullmove_number))
    return " ".join(builder)

def get_best_moves(board):
    engine.position(board)
    best_moves = []
    best_score = -100000
    is_mate = False
    result = engine.go(depth=4, mate=100)  # Gets tuple of bestmove and ponder move.
    scores = handler.info['score']
    pvs = handler.info['pv']
    for k in scores:
        score = scores[k]
        if score.mate is None or score.mate < 0:
            if not is_mate:
                if score.mate is not None:
                    cp = -100000 - score.mate
                else:
                    cp = score.cp
                if cp > best_score:
                    del best_moves[:]
                    best_score = cp
                    best_moves.append(pvs[k])
                elif cp == best_score:
                    best_moves.append(pvs[k])
        else:  # is mate
            mate = score.mate
            if not is_mate or mate < best_score:
                is_mate = True
                del best_moves[:]
                best_score = mate
                best_moves.append(pvs[k])
            elif mate == best_score:
                best_moves.append(pvs[k])
    return best_moves


engine = chess.uci.popen_engine("D:\\juegos\\stockfish_8\\stockfish_8_x64_popcnt.exe")
engine.uci()
engine.setoption({'MultiPV': 128, 'Threads': 7})
handler = chess.uci.InfoHandler()
engine.info_handlers.append(handler)


liTactics = read_level("C:\\Users\\Alfonso\\workspace_luna\\lucaschess_11\\Trainings\\mate2.fns")

print "liTactics size " + str(liTactics.__sizeof__())

def clone_board(board):
    return chess.Board(board.fen())

def check_tactica(tactica, i):
    tactica.fen = tactica.fen.replace("  - 0 1", " - - 0 1");
    tactica.pgn = tactica.pgn.replace("1-0", "");
    tactica.pgn = tactica.pgn.replace("0-1", "");
    dicFen, nDicMoves = PGN.leeEntDirigidoBaseM2(tactica.fen, tactica.pgn)

    board = chess.Board(tactica.fen)

    while nDicMoves > 0:

        best_moves = get_best_moves(board)
        jugadas_str, _ = judge(best_moves, board, dicFen, handler, i, tactica)

        move = jugadas_str[0]
        board.push_uci(move)
        nDicMoves -= 1

        if nDicMoves>0:
            best_moves = get_best_moves(board)
            jugadas_str, matches = judge(best_moves, board, dicFen, handler, i, tactica)

            if not matches:
                board_tmp = clone_board(board)
                best_new_num_moves = 99999
                select = []
                for move in best_moves :
                    uci = move[0].uci()
                    board_tmp.push_uci(uci)
                    new_best_moves = get_best_moves(board_tmp)
                    num_moves = new_best_moves.__len__()
                    if num_moves < best_new_num_moves:
                        del select[:]
                        best_new_num_moves = num_moves
                    if num_moves <= best_new_num_moves:
                        select.append(move)
                    board_tmp.pop()

                print map(lambda x: board.san(x[0]), select)
                # jugadas_str, _ = judge(select, board, dicFen, handler, i, tactica)

            move = jugadas_str[0]
            board.push_uci(move)
            nDicMoves -= 1

        # if nDicMoves>1:
        #     fen = oldstyle_fen(board)
        #     jugadas = dicFen.get(truncFen(fen))
        #     move = jugadas[0][1].movimiento().lower()
        #     board.push_uci(move)
        #
        # nDicMoves-=1

def judge(best_moves, board, dicFen, handler, i, tactica):
    best_moves_str = map(lambda x: x[0].uci(), best_moves)
    best_moves_san = map(lambda x: board.san(x[0]), best_moves)
    best_moves_san_str = ""
    for san in best_moves_san:
        best_moves_san_str += "(%d.%s)" % (board.fullmove_number, san)
    moves_san_str = ""
    for pv in handler.info['pv']:
        moves_san_str += "(%d.%s) " % (board.fullmove_number, board.san(handler.info['pv'][pv][0]))
    jugadas = dicFen.get(truncFen(oldstyle_fen(board)))
    jugadas_str = map(lambda x: x[1].movimiento().lower(), jugadas)
    tactica_str = "tactic #%d %s" % (i + 1, tactica.label)

    matches = False
    if len(jugadas) != len(best_moves):
        print "%s  len(jugadas) %d != len(best_moves) %d | %s != %s" % (
        tactica_str, len(jugadas), len(best_moves_str),map(lambda x: x[1].pgnBase, jugadas), best_moves_san_str)
        print "scores %s" % handler.info['score']
    else:
        matches = True
        for jugada in jugadas_str:
            if not jugada in best_moves_str:
                matches = False
                break
        if not matches:
            print "%s jugadas not matches best_moves" % tactica_str
            print "jugadas %s" % jugadas_str
            print "best_moves %s" % best_moves_san_str
            print "scores %s" % handler.info['score']
            print "moves %s" % moves_san_str
        else:
            print "%s | %s is OK" % (tactica_str, san)
    return jugadas_str, matches



# i = 51
# check_tactica(liTactics[i], i)

end = len(liTactics) - 1
# arr = range(106,end)
# arr = range(492,495)
arr = range(0,100)
#arr = [27]
for i in arr:
    tactica = liTactics[i]
    check_tactica(tactica, i)
    print


print "end"
